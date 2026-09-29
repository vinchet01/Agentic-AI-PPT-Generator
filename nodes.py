from dotenv import load_dotenv

from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode

from pydantic import BaseModel
from typing import Optional
import react
from react import tools, imageapi
from ppts import generate_ppt

from systemmessages import (
    SUBTOPIC_MESSAGE,
    PUT_SUBTOPIC_IN_PYDANTIC_MESSAGE,
    RESEARCH_FILTERING_MESSAGE,
    SLIDE_WRITING_MESSAGE,
    PUT_SUBTOPIC_CONTENT_IN_PYDANTIC_MESSAGE,
    LAYOUTS_FOR_3POINTS,
    LAYOUTS_FOR_4POINTS,
)

load_dotenv()



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




class WorkerState(MessagesState):
    topic: str
    subtopic: str

    research_finding: Optional[str] = None
    slidecontentinmessageform: Optional[str] = None

    # Final Pydantic result of ONE slide
    slide_content_structured: Optional[bulletListforOneSlide] = None



class PPTState(MessagesState):
    topic: str
    num_slides: int

    subtopicsinmessageform: Optional[str] = None
    subtopiclist: Optional[list[str]] = None

    subtopicscontentlist: Optional[
        list[bulletListforOneSlide]
    ] = None

    layoutslist: Optional[list[int]] = None



def subtopics_writer(state: PPTState) -> PPTState:

    subtopics = react.llmbt.invoke([
        {
            "role": "system",
            "content": SUBTOPIC_MESSAGE.format(
                topic=state["topic"],
                num_slides=state["num_slides"]
            )
        },
        *state["messages"]
    ])

    if subtopics.tool_calls:
        return {
            "messages": [subtopics]
        }


    return {
        "messages": [subtopics],
        "subtopicsinmessageform": subtopics.content
    }



def putsubtopics_in_pydantic(state: PPTState) -> PPTState:

    structured_llm = react.llm.with_structured_output(
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



def subtopic_content_writer(state: WorkerState) -> WorkerState:

    response = react.llmbt.invoke([
        {
            "role": "system",
            "content": RESEARCH_FILTERING_MESSAGE.format(
                topic=state["topic"],
                subtopic=state["subtopic"]
            )
        },
        *state["messages"]
    ])

    if response.tool_calls:
        return {
            "messages": [response]
        }

    return {
        "messages": [response],
        "research_finding": response.content
    }



def slide_writer(state: WorkerState) -> WorkerState:

    slide_response = react.llm.invoke([
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

# def slide_writer(state: WorkerState) -> WorkerState:
#     results = imageapi.search({
#   "engine": "google_images",
#   "location": "Austin, Texas, United States",
#   "google_domain": "google.com",
#   "hl": "en",
#   "gl": "us",
#   "q": "types of machine learning algorithms"
#     })
#     images_results = results["images_results"]


#     return


def put_content_in_pydantic(
    state: WorkerState
) -> WorkerState:

    structured_llm = react.llm.with_structured_output(
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


def layout_selector(state: PPTState) -> PPTState:

    structured_llm = react.llm.with_structured_output(
        LayoutSelection
    )

    layoutselectionlist = []

    for slide in state["subtopicscontentlist"]:


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


def generate_final_ppt(state: PPTState):

    subtopics = state["subtopiclist"]
    contents = state["subtopicscontentlist"]
    layouts = state["layoutslist"]

    if not (
        len(subtopics)
        == len(contents)
        == len(layouts)
    ):
        raise ValueError(
            f"Mismatch: "
            f"{len(subtopics)} subtopics, "
            f"{len(contents)} contents, "
            f"{len(layouts)} layouts"
        )

    generate_ppt(
        topic=state["topic"],
        subtopics=subtopics,
        contents=contents,
        layouts=layouts
    )

    return state




tool_node = ToolNode(tools)