import streamlit as st
from main import app
from pydantic import BaseModel
from react import llm
from systemmessages import QUERY_STRUCTURING

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


class userinputstructure(BaseModel):
    topic:str
    num_slides:int

structured_llm=llm.with_structured_output(userinputstructure)



if user_input:
    # add user message to history and print it
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    
    
    query_object=structured_llm.invoke([
        {
            "role": "system",
            "content": QUERY_STRUCTURING.format(
                userinput=user_input
            )
        }
    ])

    assistant_message = (
    f"Generating a {query_object.num_slides}-slide presentation "
    f"on **{query_object.topic}**..."
    )



    # call the ppt agent
    st.session_state['message_history'].append({'role':'assistant','content':assistant_message})
    with st.chat_message('assistant'):
        st.markdown(assistant_message)
        app.invoke({
        "topic": query_object.topic,
        "num_slides": query_object.num_slides,
        "messages": []
    })
        
    

    