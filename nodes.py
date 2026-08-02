from dotenv import load_dotenv

from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from typing import Optional

from react import llm,llmbt, tools
from ppts import generate_ppt
load_dotenv()

class SubtopicList(BaseModel):
    subtopiclist:list[str]

class bullet(BaseModel):
    bullethead:str
    bulletcontent:str

class bulletListforOneSlide(BaseModel):
    bullets:list[bullet]

class SubtopicContentList(BaseModel):
    subtopiccontentlist:list[bulletListforOneSlide]

class LayoutSelection(BaseModel):
    layout:int


class PPTContent(BaseModel):
    intro_title: str
    subtopics:list[str]
    subtopicContentList:list[bulletListforOneSlide]
    ending_line: str
    layoutselect:list[int]

class PPTState(MessagesState):
    topic: str
    num_slides: int
    subtopicsinmessageform: Optional[str] = None
    subtopiclist:Optional[list[str]] = None
    subtopicscontentinmessageform:Optional[str] = None
    subtopicscontentlist:Optional[list[bulletListforOneSlide]] = None
    layoutslist:Optional[list[int]]=None
    ppt_content: Optional[PPTContent] = None




SUBTOPIC_MESSAGE = """
You are an expert presentation content strategist with access to the Tavily web search tool.

Topic: {topic}
Number of body slides: {num_slides}

Your task is to create exactly {num_slides} subtopics for the body slides of a presentation.

========================
RESEARCH INSTRUCTIONS
========================

You MUST use the Tavily search tool before generating any subtopics.

Research strategy:

1. Perform ONE broad search about the overall topic.
2. If the first search is insufficient, perform AT MOST ONE additional broad search.
3. Do NOT perform separate searches for individual subtopics.
4. Use the information gathered from the broad search(es) to generate all the subtopics.

The goal of the search is to understand the topic as a whole before planning the presentation.

========================
SUBTOPIC REQUIREMENTS
========================

Generate exactly {num_slides} distinct subtopics.

The subtopics must:

- Cover the topic completely.
- Follow a logical presentation flow.
- Build naturally on one another.
- Be specific and non-overlapping.
- Be engaging and presentation-friendly.
- Be based on the information obtained during the broad search.
- Avoid generic or repetitive titles.

A good presentation should progress like this:

Introduction/Background
        ↓
Core concepts or analysis
        ↓
Important comparisons or insights
        ↓
Applications, impact, or future
        ↓
Conclusion

Choose the most suitable progression depending on the topic.

========================
PRESENTATION STRUCTURE
========================

Intro Slide

Body Slide 1
Body Slide 2
...
Body Slide {num_slides}

Ending Slide

Only generate the body slide subtopics.

========================
OUTPUT FORMAT
========================

Return ONLY the subtopics in the following format:

1) Subtopic 1
2) Subtopic 2
3) Subtopic 3
...
{num_slides}) Subtopic {num_slides}

Do not include explanations, reasoning, markdown, or any other text.
"""



def subtopics_writer(state:PPTState) ->PPTState:
    subtopics= llmbt.invoke([{"role": "system", "content": SUBTOPIC_MESSAGE.format(
        topic=state["topic"],
        num_slides=state["num_slides"]
    )}, *state["messages"]])
    
    return {
        "messages":[subtopics],
        "subtopicsinmessageform": subtopics.content
        }

PUT_SUBTOPIC_IN_PYDANTIC_MESSAGE="""
You are a data extraction assistant.

Subtopics List: {subtopics}

Your job is to read the given Subtopics List and convert it into the
following structured format.


1)<subtopic 1>
2)<subtopic 2>
3)<subtopic 3>
.....

Extract the values exactly as written.

Rules:
- subtopics must contain ONLY the subtopic titles in the same order.
- Do NOT include the numbering (1), 2), and the <> brackets etc.).
- subtopicContent MUST be an empty list.
- Do not rewrite, summarize or improve the text.
- Preserve the original wording.

Return ONLY the structured output.
"""

def putsubtopics_in_pydantic(state:PPTState)-> PPTState:
    subtopics=state["subtopicsinmessageform"]
    structured_llm=llm.with_structured_output(SubtopicList)
    subtopic_list= structured_llm.invoke([{"role": "system", "content":PUT_SUBTOPIC_IN_PYDANTIC_MESSAGE.format(
        subtopics=subtopics
        )}
        , *state["messages"]])
    
    return {"subtopiclist":subtopic_list.subtopiclist}


SUBTOPIC_CONTENT_MESSAGE = """
You are an expert presentation content writer.

Overall topic:
{topic}

Current subtopic:
{subtopic}

The Tavily search results for this subtopic have already been provided.

Your task is to create the content for ONLY this slide.

========================
CONTENT REQUIREMENTS
========================

Use ONLY the provided Tavily search results.

Generate either 3 or 4 bullet points.

Choose the number of bullet points that best explains the subtopic.

Use 3 bullet points when:
- three key ideas sufficiently explain the topic
- additional points would be repetitive

Use 4 bullet points when:
- the topic naturally contains four important ideas
- another point significantly improves understanding
- multiple features, comparisons, or statistics deserve separate bullets

For every bullet provide:

- Heading
- Content

Rules:

- Heading should be short and descriptive.
- Content should be concise (maximum about 2 lines).
- Every bullet should convey one distinct idea.
- Do not repeat information.
- Do not invent facts or statistics.
- Base every bullet only on the provided Tavily search results.

========================
OUTPUT FORMAT
========================

Heading 1: <heading>
Content 1: <content>

Heading 2: <heading>
Content 2: <content>

Heading 3: <heading>
Content 3: <content>

If a fourth bullet is appropriate:

Heading 4: <heading>
Content 4: <content>

========================
IMPORTANT
========================

- Generate content for ONLY the current subtopic.
- Do NOT mention or generate content for any other subtopics.
- Produce either exactly 3 or exactly 4 bullet points.
- Return ONLY the formatted content.
- Do not include explanations, reasoning, markdown, or extra text.
"""

PUT_SUBTOPIC_CONTENT_IN_PYDANTIC_MESSAGE = """
You are a data extraction assistant.

Slide content:

{subtopicwithcontent}

Extract the values exactly as written.

Rules:

- Focus only on the Heading and Content lines.
- Create either 3 or 4 Bullet objects depending on the input.
- If Heading 4 and Content 4 are present, create a fourth Bullet object.
- Otherwise, create only 3 Bullet objects.
- Each Bullet object's `bullethead` must contain only the heading text.
- Each Bullet object's `bulletcontent` must contain only the corresponding content text.
- Preserve the original wording exactly.
- Do NOT rewrite, summarize, improve, reorder, or omit any information.
- Return ONLY the structured output matching the `bulletListforOneSlide` schema.
"""


tavily_tool = next(t for t in tools if "tavily" in t.name.lower())

QUERY_GENERATION_MESSAGE = """
Given the overall topic and one subtopic of a presentation, write ONE concise, 
specific web search query that would find the most relevant, up-to-date information.

Topic: {topic}
Subtopic: {subtopic}

Return ONLY the search query text, nothing else.
"""


def subtopics_content_writer(state: PPTState) -> PPTState:
    subtopics_list = state["subtopiclist"]
    subtopic_content_list = []

    for subtopic in subtopics_list:

        query_msg = llm.invoke([
            {"role": "system", "content": QUERY_GENERATION_MESSAGE.format(
                topic=state["topic"], subtopic=subtopic)}
        ])
        search_query = query_msg.content.strip()

        search_results = tavily_tool.invoke({"query": search_query})

        content_msg = llm.invoke([
            {"role": "system", "content": SUBTOPIC_CONTENT_MESSAGE.format(
                topic=state["topic"], subtopic=subtopic)},
            {"role": "user", "content": f"Search results for '{search_query}':\n{search_results}"}
        ])

        structured_llm = llm.with_structured_output(bulletListforOneSlide)
        subtopic_content = structured_llm.invoke([
            {"role": "system", "content": PUT_SUBTOPIC_CONTENT_IN_PYDANTIC_MESSAGE.format(
                subtopicwithcontent=content_msg.content)}
        ])

        subtopic_content_list.append(subtopic_content)

    return {"subtopicscontentlist": subtopic_content_list}



LAYOUTS_FOR_3POINTS = """
You are an expert presentation slide layout selection assistant.

You are given the content of ONE slide:

{slidecontent}

DO NOT CALL ANY TOOLS.

This slide contains EXACTLY THREE bullet points.

Therefore, you MUST choose ONLY one of the following layouts.

==================================================
LAYOUT 1 — Timeline
==================================================

Choose Layout 1 when the three bullet points represent:

- a sequence
- a process
- a timeline
- stages
- cause → effect
- three equally important ideas
- information that naturally flows from left to right
- comparisons where all three points have equal importance

==================================================
LAYOUT 2 — Stacked
==================================================

Choose Layout 2 when the three bullet points represent:

- explanations
- definitions
- descriptive information
- features
- advantages/disadvantages
- independent facts
- information that is easier to read vertically
- one point contains slightly more detail than the others

==================================================
RULES
==================================================

- The slide has EXACTLY 3 bullets.
- NEVER choose any layout other than 1 or 2.
- Choose the layout that gives the most balanced and readable presentation.
- Base your decision on the meaning of the content, not randomly.

==================================================
OUTPUT
==================================================

Return ONLY the structured output.

The output must match the LayoutSelection schema.

Do not return explanations, reasoning, markdown, labels, or extra text.
"""

LAYOUTS_FOR_4POINTS = """
You are an expert presentation slide layout selection assistant.

You are given the content of ONE slide:

{slidecontent}

DO NOT CALL ANY TOOLS.

This slide contains EXACTLY FOUR bullet points.

Therefore, you MUST choose ONLY one of the following layouts.

==================================================
LAYOUT 3 — Timeline
==================================================

Choose Layout 3 when the four bullet points represent:

- a sequence
- a workflow
- a roadmap
- a lifecycle
- chronological events
- milestones
- steps where each point naturally follows the previous one

==================================================
LAYOUT 4 — Grid
==================================================

Choose Layout 4 when the four bullet points represent:

- independent ideas
- comparisons
- categories
- features
- components
- facts
- statistics
- information that can be read in any order

==================================================
LAYOUT 5 — Stacked
==================================================

Choose Layout 5 when:

- one or more bullet points contain noticeably more information
- the content is descriptive
- readability is more important than symmetry
- detailed explanations are present
- vertical reading provides a better presentation

==================================================
RULES
==================================================

- The slide has EXACTLY 4 bullets.
- NEVER choose any layout other than 3, 4 or 5.
- Choose the layout that gives the most balanced and readable presentation.
- Base your decision on the meaning of the content, not randomly.

==================================================
OUTPUT
==================================================

Return ONLY the structured output.

The output must match the LayoutSelection schema.

Do not return explanations, reasoning, markdown, labels, or extra text.
"""


def layout_selector(state: PPTState) -> PPTState:
    structured_llm = llm.with_structured_output(LayoutSelection)

    layoutselectionlist = []
    slides = state["subtopicscontentlist"]

    for slide in slides:
        if len(slide.bullets) == 3:
            layout = structured_llm.invoke(
                [
                    {
                        "role": "system",
                        "content": LAYOUTS_FOR_3POINTS.format(
                            slidecontent=slide.model_dump_json(indent=2)
                        ),
                    },
                    *state["messages"],
                ]
            ).layout

            layoutselectionlist.append(layout)

        elif len(slide.bullets) == 4:
            layout = structured_llm.invoke(
                [
                    {
                        "role": "system",
                        "content": LAYOUTS_FOR_4POINTS.format(
                            slidecontent=slide.model_dump_json(indent=2)
                        ),
                    },
                    *state["messages"],
                ]
            ).layout

            layoutselectionlist.append(layout)

        else:
            raise ValueError(
                f"Slide has {len(slide.bullets)} bullets. Expected 3 or 4."
            )

    return {"layoutslist": layoutselectionlist}


STRUCTURING_MESSAGE = """
You are a presentation structuring assistant.

You are given:

Subtopics:
{subtopiclist}

Subtopic content:
{subtopiccontentlist}

Slide layout selections:
{layoutlist}

Your job is to construct the final presentation.

Instructions:

1. Create a short and attractive introductory title for the presentation and store it in intro_title.

2. Copy the subtopics exactly as provided into the subtopics field.
   - Do not add, remove, rename, or reorder any subtopics.

3. Copy the subtopic content exactly as provided into the subtopicContentList field.
   - Preserve every bullet head and bullet content.
   - Do not rewrite, summarize, or modify the content.

4. Copy the layout selections exactly as provided into the layoutselect field.
   - The number of layouts must equal the number of subtopics.

5. Write a short concluding sentence (1-2 lines) for the presentation and store it in ending_line.

Return only the structured presentation.
"""


def put_everything_in_pydanticmodel(state:PPTState):
    subtopics_list=state["subtopiclist"]
    subtopicscontent_list=state["subtopicscontentlist"]
    slidelayoutlist=state["layoutslist"]

    structured_llm=llm.with_structured_output(PPTContent)
    result= structured_llm.invoke([{"role": "system", "content": STRUCTURING_MESSAGE.format(
        subtopiclist=subtopics_list,
        subtopiccontentlist=subtopicscontent_list,
        layoutlist=slidelayoutlist           
    )}, *state["messages"]])
    generate_ppt(result)
    return
    

tool_node = ToolNode(tools)











