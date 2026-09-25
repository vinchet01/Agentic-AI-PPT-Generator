import streamlit as st
from main import app
from pydantic import BaseModel
from react import llm,llmbt,tools
from systemmessages import QUERY_STRUCTURING
tavily_tool=tools[0]
from typing import Optional

    
class userinputstructure(BaseModel):
    wants_ppt: bool
    topic: Optional[str] = None
    num_slides: Optional[int] = None


st.set_page_config(
    page_title="AI PPT Maker",
    page_icon="📊"
)


st.title("VPPT - your presentation assistant")

if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]





for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])




user_input=st.chat_input('Type here')





structured_llm=llm.with_structured_output(userinputstructure)


if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    
    query_object=structured_llm.invoke([
        {
            "role": "system",
            "content": QUERY_STRUCTURING.format(
                conversation=st.session_state['message_history']
            )
        }
        ])
    
    if query_object.wants_ppt and query_object.topic and query_object.num_slides:

        assistant_message = (
        f"Generating a {query_object.num_slides}-slide presentation "
        f"on **{query_object.topic}**..."
        )

        # call the ppt agent
        st.session_state['message_history'].append({'role':'assistant','content':assistant_message})
        with st.chat_message('assistant'):
           st.markdown(assistant_message)

        with st.spinner("Generating your presentation..."):
          app.invoke({
          "topic": query_object.topic,
          "num_slides": query_object.num_slides,
          "messages": []
          })

    else:
     
     ai_msg = llmbt.invoke(st.session_state['message_history'])
     if ai_msg.tool_calls:
       tool_msgs = [{"role": "tool", "content": str(tavily_tool.invoke(tc["args"])), "tool_call_id": tc["id"]} for tc in ai_msg.tool_calls]
       ai_msg = llmbt.invoke(st.session_state['message_history'] + [ai_msg] + tool_msgs)
     output = ai_msg.content
     st.session_state['message_history'].append({'role':'assistant','content':output})


     with st.chat_message('assistant'):
        st.markdown(output)




