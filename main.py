from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState, StateGraph,END

from nodes import subtopics_writer,subtopics_content_writer,layout_selector,put_everything_in_pydanticmodel,tool_node,PPTState

load_dotenv()

AGENT_REASON="agent_reason"
ACT1= "act1"
ACT2="act2"
LAST = -1
SW="Subtopics_Writer"
SCW="content_writer"
LS="layouts_selector"
PP="pydantic"


def should_continue1(state: PPTState) -> str:
    if not state["messages"][LAST].tool_calls:
        return SCW
    return ACT1

def should_continue2(state: PPTState) -> str:
    if not state["messages"][LAST].tool_calls:
        return LS
    return ACT2



flow = StateGraph(PPTState)
flow.add_node(SW, subtopics_writer)

flow.set_entry_point(SW)

flow.add_node(ACT1, tool_node)
flow.add_edge(ACT1, SW)
flow.add_node(SCW, subtopics_content_writer)

flow.add_conditional_edges(SW, should_continue1, {
    SCW:SCW,
    ACT1:ACT1})

flow.add_node(ACT2, tool_node)
flow.add_node(LS,layout_selector)
flow.add_edge(ACT2, SCW)

flow.add_conditional_edges(SCW, should_continue2, {
    LS:LS,
    ACT2:ACT2})

flow.add_node(PP,put_everything_in_pydanticmodel)
flow.add_edge(LS,PP)
flow.add_edge(PP,END)









app = flow.compile()
app.get_graph().draw_mermaid_png(output_file_path="flow.png")


if __name__ == "__main__":
    res = app.invoke({
        "topic": "swiggy vs zomato",
        "num_slides": 5,
        "messages": []
    })

