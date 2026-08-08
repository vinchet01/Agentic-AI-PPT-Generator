from dotenv import load_dotenv

from langgraph.graph import StateGraph, END

from nodes import (
    subtopics_writer,
    putsubtopics_in_pydantic,
    subtopic_content_writer,
    slide_writer,
    put_content_in_pydantic,
    layout_selector,
    put_everything_in_pydanticmodel,
    tool_node,
    PPTState,
    WorkerState
)

load_dotenv()


# =========================================================
# NODE NAMES
# =========================================================

SW = "Subtopics_Writer"
SP = "Subtopics_pydantic"

ACT1 = "act1"


SCW = "content_writer"
ACT2 = "act2"
SLW = "slide_writer"
SCP = "content_pydantic"


PROCESS = "process_all_subtopics"

LS = "layouts_selector"
PP = "ppt_content_pydantic"


# =========================================================
# ROUTING
# =========================================================

def should_continue1(state: PPTState) -> str:

    if state["messages"][-1].tool_calls:
        return ACT1

    return SP


def should_continue2(state: WorkerState) -> str:

    if state["messages"][-1].tool_calls:
        return ACT2

    return SLW


# =========================================================
# WORKER GRAPH
#
# Handles ONE subtopic.
# =========================================================

worker = StateGraph(WorkerState)


worker.add_node(
    SCW,
    subtopic_content_writer
)

worker.add_node(
    ACT2,
    tool_node
)

worker.add_node(
    SLW,
    slide_writer
)

worker.add_node(
    SCP,
    put_content_in_pydantic
)


worker.set_entry_point(SCW)


# Research:
#
# wants Tavily -> ACT2
# finished      -> slide writer

worker.add_conditional_edges(
    SCW,
    should_continue2,
    {
        ACT2: ACT2,
        SLW: SLW
    }
)


# Tavily -> Research Agent again

worker.add_edge(
    ACT2,
    SCW
)


# Research -> Slide Writing -> Pydantic

worker.add_edge(
    SLW,
    SCP
)


worker.add_edge(
    SCP,
    END
)


worker_app = worker.compile()
worker_app.get_graph().draw_mermaid_png(
    output_file_path="worker.png"
)


# =========================================================
# PROCESS ALL SUBTOPICS
#
# This is now just a simple Python loop.
# =========================================================

def process_all_subtopics(state: PPTState):

    all_slide_contents = []

    for subtopic in state["subtopiclist"]:

        result = worker_app.invoke({
            "topic": state["topic"],
            "subtopic": subtopic,
            "messages": []
        })

        all_slide_contents.append(
            result["slide_content_structured"]
        )

    return {
        "subtopicscontentlist": all_slide_contents
    }


# =========================================================
# MAIN GRAPH
# =========================================================

flow = StateGraph(PPTState)


# ---------------------------------------------------------
# SUBTOPIC WRITER
# ---------------------------------------------------------

flow.add_node(
    SW,
    subtopics_writer
)

flow.set_entry_point(SW)


# ---------------------------------------------------------
# ACT1
# Tavily for overall-topic research
# ---------------------------------------------------------

flow.add_node(
    ACT1,
    tool_node
)


flow.add_conditional_edges(
    SW,
    should_continue1,
    {
        ACT1: ACT1,
        SP: SP
    }
)


flow.add_edge(
    ACT1,
    SW
)


# ---------------------------------------------------------
# SUBTOPICS -> PYDANTIC
# ---------------------------------------------------------

flow.add_node(
    SP,
    putsubtopics_in_pydantic
)


# ---------------------------------------------------------
# PROCESS EACH SUBTOPIC
# ---------------------------------------------------------

flow.add_node(
    PROCESS,
    process_all_subtopics
)


flow.add_edge(
    SP,
    PROCESS
)


# ---------------------------------------------------------
# LAYOUT SELECTOR
# ---------------------------------------------------------

flow.add_node(
    LS,
    layout_selector
)


flow.add_edge(
    PROCESS,
    LS
)


# ---------------------------------------------------------
# FINAL PPT
# ---------------------------------------------------------

flow.add_node(
    PP,
    put_everything_in_pydanticmodel
)


flow.add_edge(
    LS,
    PP
)


flow.add_edge(
    PP,
    END
)


# =========================================================
# COMPILE
# =========================================================

app = flow.compile()


app.get_graph().draw_mermaid_png(
    output_file_path="flow.png"
)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    res = app.invoke({
        "topic": "How UPI Transformed Digital Payments in India",
        "num_slides": 5,
        "messages": []
    })
