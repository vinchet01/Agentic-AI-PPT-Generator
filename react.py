from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

load_dotenv()



tools = [TavilySearch(max_results=1)]

llmbt = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)
# llmbt = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     temperature=0
# ).bind_tools(tools)



llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     temperature=0
# )

