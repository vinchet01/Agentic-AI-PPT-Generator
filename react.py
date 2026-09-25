from dotenv import load_dotenv
import os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
import serpapi
load_dotenv()



tools = [TavilySearch(max_results=3)]


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


imageapi = serpapi.Client(
    api_key=os.getenv("SERPIMAGES_API_KEY")
)

