from dotenv import load_dotenv

from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode

from pydantic import BaseModel
from typing import Optional

from react import llm, llmbt, tools
from ppts import generate_ppt

from systemmessages import (
    SUBTOPIC_MESSAGE,
    PUT_SUBTOPIC_IN_PYDANTIC_MESSAGE,
    RESEARCH_FILTERING_MESSAGE,
    SLIDE_WRITING_MESSAGE,
    PUT_SUBTOPIC_CONTENT_IN_PYDANTIC_MESSAGE,
    LAYOUTS_FOR_3POINTS,
    LAYOUTS_FOR_4POINTS,
    STRUCTURING_MESSAGE
)

load_dotenv()


# =========================================================
# PYDANTIC MODELS
# =========================================================

class SubtopicList(BaseModel):
    subtopiclist: list[str]


class bullet(BaseModel):
    bullethead: str
    bulletcontent: str


class bulletListforOneSlide(BaseModel):
    bullets: list[bullet]


class SubtopicContentList(BaseModel):
    subtopiccontentlist: list[bulletListforOneSlide]


class LayoutSelection(BaseModel):
    layout: int


class PPTContent(BaseModel):
    intro_title: str
    subtopics: list[str]
    subtopicContentList: list[bulletListforOneSlide]
    ending_line: str
    layoutselect: list[int]


# =========================================================
# WORKER STATE
#
# Used only while researching/writing ONE slide.
# =========================================================

class WorkerState(MessagesState):
    topic: str
    subtopic: str

    research_finding: Optional[str] = None
    slidecontentinmessageform: Optional[str] = None

    # Final Pydantic result of ONE slide
    slide_content_structured: Optional[bulletListforOneSlide] = None


# =========================================================
# MAIN PPT STATE
# =========================================================

class PPTState(MessagesState):
    topic: str
    num_slides: int

    subtopicsinmessageform: Optional[str] = None
    subtopiclist: Optional[list[str]] = None

    subtopicscontentlist: Optional[
        list[bulletListforOneSlide]
    ] = None

    layoutslist: Optional[list[int]] = None

    ppt_content: Optional[PPTContent] = None


# =========================================================
# SUBTOPIC WRITER
# =========================================================

def subtopics_writer(state: PPTState) -> PPTState:

    subtopics = llmbt.invoke([
        {
            "role": "system",
            "content": SUBTOPIC_MESSAGE.format(
                topic=state["topic"],
                num_slides=state["num_slides"]
            )
        },
        *state["messages"]
    ])

    return {
        "messages": [subtopics],
        "subtopicsinmessageform": subtopics.content
    }


# =========================================================
# SUBTOPIC PYDANTIC
# =========================================================

def putsubtopics_in_pydantic(state: PPTState) -> PPTState:

    structured_llm = llm.with_structured_output(
        SubtopicList
    )

    subtopic_list = structured_llm.invoke([
        {
            "role": "system",
            "content": PUT_SUBTOPIC_IN_PYDANTIC_MESSAGE.format(
                subtopics=state["subtopicsinmessageform"]
            )
        }
    ])

    return {
        "subtopiclist": subtopic_list.subtopiclist
    }


# =========================================================
# RESEARCH ONE SUBTOPIC
# =========================================================

def subtopic_content_writer(state: WorkerState) -> WorkerState:

    response = llmbt.invoke([
        {
            "role": "system",
            "content": RESEARCH_FILTERING_MESSAGE.format(
                topic=state["topic"],
                subtopic=state["subtopic"]
            )
        },
        *state["messages"]
    ])

    # LLM wants Tavily
    if response.tool_calls:
        return {
            "messages": [response]
        }

    # Research finished
    return {
        "messages": [response],
        "research_finding": response.content
    }


# =========================================================
# WRITE ONE SLIDE
# =========================================================

def slide_writer(state: WorkerState) -> WorkerState:

    slide_response = llm.invoke([
        {
            "role": "system",
            "content": SLIDE_WRITING_MESSAGE.format(
                topic=state["topic"],
                subtopic=state["subtopic"],
                research_findings=state["research_finding"]
            )
        }
    ])

    return {
        "slidecontentinmessageform": slide_response.content
    }


# =========================================================
# CONVERT ONE SLIDE TO PYDANTIC
# =========================================================

def put_content_in_pydantic(
    state: WorkerState
) -> WorkerState:

    structured_llm = llm.with_structured_output(
        bulletListforOneSlide
    )

    slide_content = structured_llm.invoke([
        {
            "role": "system",
            "content":
                PUT_SUBTOPIC_CONTENT_IN_PYDANTIC_MESSAGE.format(
                    slidecontent=state[
                        "slidecontentinmessageform"
                    ]
                )
        }
    ])

    return {
        "slide_content_structured": slide_content
    }


# =========================================================
# LAYOUT SELECTOR
# =========================================================

def layout_selector(state: PPTState) -> PPTState:

    structured_llm = llm.with_structured_output(
        LayoutSelection
    )

    layoutselectionlist = []

    for slide in state["subtopicscontentlist"]:

        # -----------------------------
        # 3 BULLETS
        # -----------------------------

        if len(slide.bullets) == 3:

            layout = structured_llm.invoke([
                {
                    "role": "system",
                    "content": LAYOUTS_FOR_3POINTS.format(
                        slidecontent=slide.model_dump_json(
                            indent=2
                        )
                    )
                }
            ]).layout

            layoutselectionlist.append(layout)

        # -----------------------------
        # 4 BULLETS
        # -----------------------------

        elif len(slide.bullets) == 4:

            layout = structured_llm.invoke([
                {
                    "role": "system",
                    "content": LAYOUTS_FOR_4POINTS.format(
                        slidecontent=slide.model_dump_json(
                            indent=2
                        )
                    )
                }
            ]).layout

            layoutselectionlist.append(layout)

        else:

            raise ValueError(
                f"Slide has {len(slide.bullets)} bullets. "
                "Expected 3 or 4."
            )

    return {
        "layoutslist": layoutselectionlist
    }


# =========================================================
# FINAL PPT CONTENT
# =========================================================

def put_everything_in_pydanticmodel(
    state: PPTState
) -> PPTState:

    structured_llm = llm.with_structured_output(
        PPTContent
    )

    result = structured_llm.invoke([
        {
            "role": "system",
            "content": STRUCTURING_MESSAGE.format(
                subtopiclist=state["subtopiclist"],
                subtopiccontentlist=
                    state["subtopicscontentlist"],
                layoutlist=state["layoutslist"]
            )
        }
    ])

    generate_ppt(result)

    return {
        "ppt_content": result
    }


# =========================================================
# TAVILY TOOL NODE
# =========================================================

tool_node = ToolNode(tools)