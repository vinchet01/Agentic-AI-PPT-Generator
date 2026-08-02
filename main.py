from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState, StateGraph,END

from nodes import subtopics_writer,subtopics_content_writer,layout_selector,put_everything_in_pydanticmodel,tool_node,PPTState,putsubtopics_in_pydantic
load_dotenv()

AGENT_REASON="agent_reason"
ACT1= "act1"
ACT2="act2"
LAST = -1
SW="Subtopics_Writer"
SP="Subtopics_pydantic"
SCW="content_writer"
LS="layouts_selector"
PP="ppt_content_pydantic"



def should_continue1(state: PPTState) -> str:
    if not state["messages"][LAST].tool_calls:
        return SP
    return ACT1




flow = StateGraph(PPTState)
flow.add_node(SW, subtopics_writer)

flow.set_entry_point(SW)

flow.add_node(ACT1, tool_node)
flow.add_edge(ACT1, SW)

flow.add_node(SP,putsubtopics_in_pydantic)

flow.add_conditional_edges(SW, should_continue1, {
    SP:SP,
    ACT1:ACT1})
flow.add_node(SCW, subtopics_content_writer)

flow.add_edge(SP,SCW)

flow.add_node(LS,layout_selector)

flow.add_edge(SCW,LS)

flow.add_node(PP,put_everything_in_pydanticmodel)
flow.add_edge(LS,PP)
flow.add_edge(PP,END)



app = flow.compile()
app.get_graph().draw_mermaid_png(output_file_path="flow.png")



if __name__ == "__main__":
    res = app.invoke({
        "topic": "Tesla vs BYD",
        "num_slides": 7,
        "messages": []
    })

