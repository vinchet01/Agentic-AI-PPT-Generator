import streamlit as st
from pydantic import BaseModel
import os
from systemmessages import QUERY_STRUCTURING
from typing import Optional

    
class userinputstructure(BaseModel):
    wants_ppt: bool
    topic: Optional[str] = None
    num_slides: Optional[int] = None


st.set_page_config(
    page_title="Presently",
    page_icon="📊"
)


st.title("Presently - your presentation assistant")

with st.sidebar:
    st.header("🔑 API Keys")

    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-..."
    )

    tavily_api_key = st.text_input(
        "Tavily API Key",
        type="password",
        placeholder="tvly-..."
    )

    st.divider()

    st.subheader("LangSmith")
    st.caption("Optional — enable this if you want to view traces.")

    langsmith_api_key = st.text_input(
        "LangSmith API Key",
        type="password",
        placeholder="lsv2_pt_..."
    )

    langsmith_project = st.text_input(
        "Project",
        value="Presently"
    )


if not openai_api_key or not tavily_api_key:
    st.info("Please enter both API keys to continue.")
    st.stop()

os.environ["TAVILY_API_KEY"] = tavily_api_key

if langsmith_api_key:
    os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = langsmith_project or "Presently"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"


from main import app
import react
from react import tools
tavily_tool=tools[0]

react.initialize_llms(openai_api_key)


if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]





for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])




user_input=st.chat_input('Type here')





structured_llm=react.llm.with_structured_output(userinputstructure)


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

        with open("final_output.pptx", "rb") as file:
           ppt_data = file.read()

        st.success("Presentation generated successfully!")

        st.download_button(
        label="📥 Download PowerPoint",
        data=ppt_data,
        file_name="VPPT_Presentation.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )




    else:
     
     ai_msg = react.llmbt.invoke(st.session_state['message_history'])
     if ai_msg.tool_calls:
       tool_msgs = [{"role": "tool", "content": str(tavily_tool.invoke(tc["args"])), "tool_call_id": tc["id"]} for tc in ai_msg.tool_calls]
       ai_msg = react.llmbt.invoke(st.session_state['message_history'] + [ai_msg] + tool_msgs)
     output = ai_msg.content
     st.session_state['message_history'].append({'role':'assistant','content':output})


     with st.chat_message('assistant'):
        st.markdown(output)




