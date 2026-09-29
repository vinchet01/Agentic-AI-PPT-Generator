from dotenv import load_dotenv

from langgraph.graph import StateGraph, END

from nodes import (
    subtopics_writer,
    putsubtopics_in_pydantic,
    subtopic_content_writer,
    slide_writer,
    put_content_in_pydantic,
    layout_selector,
    generate_final_ppt,
    tool_node,
    PPTState,
    WorkerState
)

load_dotenv()



SW = "Subtopics_Writer"
SP = "Subtopics_pydantic"

ACT1 = "act1"


SCW = "content_writer"
ACT2 = "act2"
SLW = "slide_writer"
SCP = "content_pydantic"


PROCESS = "process_all_subtopics"

LS = "layouts_selector"
GP = "generate_ppt"



def should_continue1(state: PPTState) -> str:

    if state["messages"][-1].tool_calls:
        return ACT1

    return SP


def should_continue2(state: WorkerState) -> str:

    if state["messages"][-1].tool_calls:
        return ACT2

    return SLW



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



worker.add_conditional_edges(
    SCW,
    should_continue2,
    {
        ACT2: ACT2,
        SLW: SLW
    }
)



worker.add_edge(
    ACT2,
    SCW
)



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



flow = StateGraph(PPTState)




flow.add_node(
    SW,
    subtopics_writer
)

flow.set_entry_point(SW)




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



flow.add_node(
    SP,
    putsubtopics_in_pydantic
)




flow.add_node(
    PROCESS,
    process_all_subtopics
)


flow.add_edge(
    SP,
    PROCESS
)



flow.add_node(
    LS,
    layout_selector
)


flow.add_edge(
    PROCESS,
    LS
)

flow.add_node(
    GP,
    generate_final_ppt
)



flow.add_edge(
    LS,
    GP
)
flow.add_edge(
    GP,
    END
)



app = flow.compile()


app.get_graph().draw_mermaid_png(
    output_file_path="flow.png"
)




