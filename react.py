from dotenv import load_dotenv
import os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
import serpapi
load_dotenv()



tools = [TavilySearch(max_results=3)]


llm = None
llmbt = None


def initialize_llms(api_key):
    global llm, llmbt

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key
    )

    llmbt = llm.bind_tools(tools)




imageapi = serpapi.Client(
    api_key=os.getenv("SERPIMAGES_API_KEY")
)

