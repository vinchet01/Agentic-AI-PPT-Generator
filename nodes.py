from dotenv import load_dotenv

from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from typing import Optional

from react import llm,llmbt, tools
from ppts import generate_ppt
load_dotenv()


class bullet(BaseModel):
    bullethead:str
    bulletcontent:str

class bulletListforOneSlide(BaseModel):
    bullets:list[bullet]

class LayoutSelection(BaseModel):
    layout:int

class PPTContent(BaseModel):
    intro_title: str
    subtopics:list[str]
    subtopicContent: list[bulletListforOneSlide]
    ending_line: str
    layoutselect:list[int]

class PPTState(MessagesState):
    topic: str
    num_slides: int
    ppt_content: Optional[PPTContent] = None



structured_llm=llm.with_structured_output(PPTContent);






SUBTOPIC_MESSAGE = """
You are an expert presentation content strategist with access to a web search tool (Tavily).

Topic: {topic}
Number of slides: {num_slides}

You MUST use the search tool to research the topic before proposing subtopics. Do not rely on 
your own training data or prior knowledge — the topic may involve recent events, current data, 
or fast-changing information that you are not aware of. Call the search tool at least once 
before producing your final answer.

Based on what you find, come up with exactly {num_slides} subtopics, one for each slide, that 
together tell a complete and compelling story about the topic — not just a random list of 
related points.


The subtopics must:
- Follow a logical, natural order (e.g. introduction/context → core aspects → comparison/ 
  deeper insight → impact or conclusion), so the presentation flows like a narrative, not a 
  list of facts thrown together.
- Each build on the previous one, so a viewer going slide by slide feels like they're 
  progressing somewhere, not jumping between disconnected ideas.
- Be specific and non-overlapping — no two subtopics should cover the same ground.
- Be grounded in what your search actually returned, not assumptions.
- Together fully justify and represent the topic, so someone reading only the subtopic titles 
  understands the shape of the whole presentation.
- Be phrased in a way that is engaging and presentation-worthy — avoid dry, generic phrasing; 
  make each subtopic sound like something people would want to see explored.

Output ONLY the subtopics, formatted exactly like this:
1) Subtopic 1
2) Subtopic 2
3) Subtopic 3
...continue for all {num_slides} subtopics, with no extra commentary before or after.

You must generate exactly {num_slides} distinct subtopics.
Before generating them, use the Tavily tool as many times as necessary until you have enough information.
Do not stop until you have produced exactly {num_slides} subtopics.
"""

SUBTOPIC_CONTENT_MESSAGE = """
you have this subtopic list {subtopics}
(Overall topic for context: {topic})

for the intro slide write a catchy intro title below:
intro_title:<intro_title>
for last slide write a conclusion line below:
ending_line:<ending_line>

Follow this steps:
Step 1:take the first subtopic search tavily and get results
Step 2:using the results write in this format:

Subtopic 1: <subtopic 1>
Heading 1: <heading>
Content 1: <content>
Heading 2: <heading>
Content 2: <content>
Heading 3: <heading>
Content 3: <content>

If generating a fourth point:

Heading 4: <heading>
Content 4: <content>

repeat the step 1 and step 2 for all further subtopics

"""

SLIDELAYOUT_SELECTION_MESSAGE="""
You are a slide layout selection assistant.
Your job is to select the most suitable layout for every slide.
You are given the contents of all slides:
{slidecontent}
DO NOT DO ANY TOOL CALLS HERE.
Available layouts:

Layouts for 3 points:
1) 3 points side by side of a line
2) 3 points one below the other on the left side of the slide

Layouts for 4 points:
3) 4 points side by side of a line
4) 4 points arranged in a square
5) 4 points one below the other on the left side of the slide

Rules:
- Process each slide independently.
- Determine whether the slide contains 3 or 4 points.
- If the slide has 3 points, choose only Layout 1 or Layout 2.
- If the slide has 4 points, choose only Layout 3, Layout 4, or Layout 5.
- Choose the layout that best fits the amount and length of the content and produces a balanced, readable slide.

Output exactly one line for each slide in the following format:

layoutslide1:<number>
layoutslide2:<number>
layoutslide3:<number>
...

Continue until every slide has a layout.

Return just the layout selections.
"""

STRUCTURING_MESSAGE = """
You are a data structuring assistant.

Your job is to read the given content and convert it into the
PPTContent structured format.

You are given:

Subtopics and their contents:
{subtopics_content}

Layout selections:
{layouts}

Rules:

- Extract the intro title.
- Extract the ending line.
- Create the subtopics list in the same order as they appear.
- For each subtopic, create one BulletList.
- Each BulletList should contain 3 or 4 Bullet objects.
- bullethead must contain only the heading text.
- bulletcontent must contain only the corresponding content text.
- Create the layoutselect list using the layout numbers in the same order as the subtopics.
- The lengths of subtopics, subtopicContent, and layoutselect must always be equal.
- Preserve the original wording exactly.
- Do NOT rewrite, summarize, improve, or invent any information.
- Return ONLY the structured output matching the PPTContent schema.
"""




def subtopics_writer(state:PPTState) ->PPTState:
    subtopics= llmbt.invoke([{"role": "system", "content": SUBTOPIC_MESSAGE.format(
        topic=state["topic"],
        num_slides=state["num_slides"]
    )}, *state["messages"]])
    
    return {"messages": [subtopics]}

def subtopics_content_writer(state:PPTState) ->PPTState:
    subtopics=state["messages"][-1].content
    subtopics_content= llmbt.invoke([{"role": "system", "content":SUBTOPIC_CONTENT_MESSAGE.format(
        subtopics=subtopics,
        topic=state["topic"])}
        , *state["messages"]])
    return {"messages": [subtopics_content]}

def layout_selector(state:PPTState) ->PPTState:
    subtopics_content=state["messages"][-1].content
    layouts= llm.invoke([{"role": "system", "content": SLIDELAYOUT_SELECTION_MESSAGE.format(
        slidecontent=subtopics_content
    )}, *state["messages"]])
    return {"messages": [layouts]}

def put_everything_in_pydanticmodel(state:PPTState):
    layouts=state["messages"][-1].content
    subtopics_content=state["messages"][-2].content
    result= structured_llm.invoke([{"role": "system", "content": STRUCTURING_MESSAGE.format(
        subtopics_content=subtopics_content,
        layouts=layouts
    )}, *state["messages"]])
    generate_ppt(result)
    return
    



tool_node = ToolNode(tools)
