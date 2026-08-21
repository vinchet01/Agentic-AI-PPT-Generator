
# Presently — Agentic AI Presentation Generator

Presently is an AI-powered PowerPoint generation system that researches a topic, plans presentation subtopics, researches each slide independently, generates concise slide content, dynamically selects suitable layouts, and creates a complete `.pptx` presentation.

Unlike a simple prompt-to-PPT generator, Presently uses an **agentic research workflow built with LangGraph**, where the LLM can independently use web search tools to gather relevant information before writing each slide.

## ✨ Features

* 💬 Natural-language presentation requests
* 🔎 Web research using Tavily Search
* 🤖 LLM-controlled tool calling using LangChain
* 🧠 Automatic presentation subtopic generation
* 🔬 Independent research for every slide
* ✍️ Research-to-slide content generation
* 📋 Structured outputs using Pydantic
* 🎨 Dynamic slide layout selection
* 📊 Automatic PowerPoint generation using `python-pptx`
* 💬 Chat-style Streamlit interface
* 🖼️ SerpAPI integration for image search *(under development)*

## 🧠 How It Works

A user can enter a request such as:

> Create a 6-slide presentation about how AI is transforming healthcare.

Presently first extracts:

```text
Topic: How AI is transforming healthcare
Number of slides: 6
```

The request is then passed to the LangGraph presentation pipeline.

### Main Graph

```text
START
  │
  ▼
Subtopic Writer
  │
  ├──── needs research ────► Tavily (ACT1)
  │                              │
  ◄───────────────────────────────┘
  │
  ▼
Subtopic Pydantic
  │
  ▼
Process All Subtopics
  │
  │  Calls the worker graph
  │  once for each subtopic
  │
  ▼
Layout Selector
  │
  ▼
Final PPT Content
  │
  ▼
PowerPoint Generation
  │
  ▼
END
```

### Worker Graph

Every presentation subtopic is independently processed by a worker graph.

```text
START
  │
  ▼
Research Agent
  │
  ├──── needs more information ───► Tavily (ACT2)
  │                                      │
  ◄───────────────────────────────────────┘
  │
  │ Research complete
  ▼
Slide Writer
  │
  ▼
Content Pydantic
  │
  ▼
END
```

This allows the research agent to decide when and what to search instead of relying on a fixed search query.

## 🔄 Presentation Generation Flow

```text
User Query
    ↓
Extract Topic + Number of Slides
    ↓
Generate Presentation Subtopics
    ↓
Research Each Subtopic
    ↓
Filter Important Research Findings
    ↓
Write Slide Content
    ↓
Convert Content to Structured Pydantic Models
    ↓
Select Suitable Slide Layouts
    ↓
Generate PowerPoint
    ↓
.pptx Presentation
```

## 🛠️ Tech Stack

| Technology    | Purpose                          |
| ------------- | -------------------------------- |
| Python        | Core application                 |
| LangGraph     | Agent workflow orchestration     |
| LangChain     | LLM and tool integration         |
| OpenAI        | Content generation and reasoning |
| Tavily        | Web research                     |
| SerpAPI       | Image search                     |
| Pydantic      | Structured LLM outputs           |
| python-pptx   | PowerPoint generation            |
| Streamlit     | Chat-style user interface        |
| python-dotenv | Environment variable management  |


## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vinchet01/Agentic-AI-PPT-Generator.git
cd Agentic-AI-PPT-Generator
```

### 2. Install Dependencies

This project uses `uv` for dependency management.

Install `uv` if it is not already installed, then run:

```bash
uv sync
```

If you are adding dependencies manually, the main packages used by the project include:

```bash
uv add langgraph langchain langchain-openai langchain-tavily
uv add python-pptx pydantic python-dotenv
uv add streamlit serpapi
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
SERPIMAGES_API_KEY=your_serpapi_key
```


### 4. Run the Streamlit Application

```bash
streamlit run streamlitapp.py
```

Or with `uv`:

```bash
uv run streamlit run streamlitapp.py
```

Streamlit will provide a local address, typically:

```text
http://localhost:8501
```

Open it in your browser to use Presently.

## 💬 Example

Enter a natural-language request:

```text
Make a 7-slide presentation about the global race for humanoid robots.
```

Presently extracts the presentation requirements and sends them to the generation pipeline.

The system then:

1. Researches the overall topic.
2. Creates logically ordered subtopics.
3. Independently researches every subtopic.
4. Selects the most valuable findings.
5. Converts the research into presentation-friendly content.
6. Chooses appropriate slide layouts.
7. Generates the final PowerPoint presentation.

## 🎯 Why Agentic Research?

A conventional PPT generator might ask an LLM to directly generate all slide content from its existing knowledge.

Presently separates **research from writing**.

```text
Traditional approach:

Topic → LLM → Slides


Presently:

Topic
  ↓
Planning
  ↓
Research Agent ↔ Web Search
  ↓
Research Findings
  ↓
Slide Writer
  ↓
Structured Content
  ↓
Layout Selection
  ↓
PowerPoint
```

The research agent can decide what information it needs and use Tavily multiple times before finalizing its findings.

This produces more specific and informative slide content while reducing generic or repetitive points.

## 🚧 Planned Improvements

* Interactive subtopic approval and editing
* Slide content preview and editing
* Google image search using SerpAPI
* User-controlled image selection
* Image integration into slide layouts
* Slide previews before export
* Regenerate individual slides
* Change layouts interactively
* React-based interactive presentation editor
* FastAPI backend
* Improved presentation customization

## 📌 Current Status

Presently currently supports the complete core generation pipeline:

**Topic → Research → Subtopics → Per-slide Research → Slide Content → Dynamic Layout Selection → PowerPoint Generation**

The next phase focuses on adding greater **human-in-the-loop control**, allowing users to review and modify the outline, slide content, images, and layouts before generating the final presentation.

## 👨‍💻 Author

**Vinayagam Chetiyar**

Built as an exploration of agentic AI, automated research, structured generation, and programmatic presentation creation.


<img width="304" height="630" alt="flow" src="https://github.com/user-attachments/assets/e9e479f8-6f14-480a-a6d1-a2951080b9a8" />

<img width="257" height="432" alt="worker" src="https://github.com/user-attachments/assets/0dfde266-15db-4b41-aa1c-ec5929f86bd6" />

