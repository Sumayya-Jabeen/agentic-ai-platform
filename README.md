# Agentic AI Platform

An AI-powered agentic client platform with modular skill routing, real-time streaming, and a full-featured chat interface. The system automatically understands user intent and routes requests to the appropriate AI skill — Research & Summarization or Task Planning & Execution — before delivering a structured, streamed response.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Skills](#skills)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Running the Platform](#running-the-platform)
- [API Reference](#api-reference)
- [Frontend Features](#frontend-features)
- [Contributors](#contributors)

---

## Overview

This platform is **not a simple chatbot**. It is a modular, agentic AI system where:

- A **LangChain-powered Orchestrator** acts as the brain — it reads the user's message and automatically decides which skill to invoke
- The **Research Skill** searches the web in multiple passes and synthesizes a structured, source-cited summary
- The **Task Planning Skill** breaks any goal into an ordered, dependency-aware action plan
- The **Frontend** streams responses token-by-token, renders full Markdown, and manages conversation sessions

---

## Architecture

```
User / Browser
      │
      ▼
Frontend  (Next.js · TypeScript · Tailwind CSS)
  ChatWindow · InputBar · Sidebar · useChat hook
      │
      │  POST /chat/stream  ·  POST /research  ·  POST /plan
      ▼
Backend  (FastAPI · Python)
  Middleware: Auth (X-API-Key) · CORS · Request Logging
  Routes: /chat/stream · /research · /plan · /health · /sessions
  Session Management: ConversationHistory (in-memory)
      │
      ▼
Orchestrator  (LangChain Agent)
  Auto-routes based on user intent
  ┌─────────────────────┐   ┌──────────────────────────┐
  │  Research Skill      │   │  Task Planning Skill      │
  │  Phase 1: Web search │   │  Step 1: Plan generation  │
  │  Phase 2: Synthesis  │   │  Step 2: Execution        │
  └─────────────────────┘   └──────────────────────────┘
      │                              │
      ▼                              ▼
  Tavily Search API            OpenAI API (GPT)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+ |
| AI Orchestration | LangChain, LangChain-OpenAI |
| LLM | OpenAI GPT (configurable model) |
| Web Search | Tavily Search API |
| Data Validation | Pydantic v2 |
| Streaming | Server-Sent Events (SSE) |
| Auth | API Key (`X-API-Key` header) |
| Session Storage | In-memory (ConversationHistory) |

---

## Project Structure

```
agentic-ai-platform/
│
├── api/                        # FastAPI application
│   ├── main.py                 # App entry point, middleware registration
│   ├── middleware/
│   │   ├── auth.py             # API key authentication
│   │   └── logging.py          # Request/response logging middleware
│   ├── models/
│   │   └── requests.py         # FastAPI request/response models
│   ├── routes/
│   │   ├── chat.py             # /chat, /sessions, /history endpoints
│   │   ├── research.py         # /research direct skill endpoint
│   │   └── plan.py             # /plan direct skill endpoint
│   └── services/
│       └── history.py          # In-memory conversation session manager
│
├── skills/
│   ├── research.py             # Research & Summarization Skill
│   └── task_planner.py         # Task Planning & Execution Skill
│
├── tools/
│   ├── web_search.py           # Tavily web search tool wrapper
│   └── executor.py             # Task execution engine
│
├── orchestrator.py             # LangChain agent — routes to skills
├── models.py                   # Pydantic input/output schemas for skills
├── callbacks.py                # LangChain pipeline logging callbacks
├── config.py                   # Environment config loader
│
├── frontend/                   # Next.js application
│   ├── app/
│   │   ├── chat/page.tsx       # Main chat page
│   │   ├── layout.tsx          # Root layout
│   │   └── globals.css         # Global styles + Markdown CSS
│   ├── components/
│   │   ├── ChatWindow.tsx      # Message list + pinned messages bar
│   │   ├── MessageBubble.tsx   # Individual message with Markdown rendering
│   │   ├── InputBar.tsx        # Text input with voice and file attachment
│   │   └── Sidebar.tsx         # Session history with search, pin, rename
│   ├── hooks/
│   │   └── useChat.ts          # Core chat state, streaming, session logic
│   └── lib/
│       ├── api.ts              # API client functions
│       └── types.ts            # Shared TypeScript types
│
├── .env                        # Secret keys (never commit this)
├── requirements.txt            # Python dependencies
├── architecture_diagram.html   # System architecture diagram
└── README.md
```

---

## Skills

### 1. Research & Summarization Skill

Triggered automatically when the user asks about a topic, technology, or wants information gathered.

**How it works:**
- **Phase 1 — Information Gathering:** A LangChain agent runs a web search loop (3–5 searches via Tavily), autonomously deciding what to search and when it has enough information
- **Phase 2 — Synthesis:** The gathered context is passed to GPT with `with_structured_output()` which enforces a strict `ResearchOutput` Pydantic schema

**Input schema (`ResearchInput`):**
```python
query: str                          # Topic or question to research
focus_areas: Optional[List[str]]    # Narrow to specific sub-topics
output_format: OutputFormat         # bullet_points | paragraph | structured
```

**Output schema (`ResearchOutput`):**
```python
summary: str                        # Comprehensive summary
key_points: List[str]               # Bullet-point findings
sources: List[Source]               # URLs, titles, credibility scores
gaps: List[str]                     # What could not be found
confidence: float                   # 0.0 – 1.0 confidence score
```

---

### 2. Task Planning & Execution Skill

Triggered automatically when the user asks for a plan, roadmap, or steps to accomplish a goal.

**How it works:**
- **Step 1 — Plan Generation:** GPT with `with_structured_output()` returns a fully validated `TaskPlanOutput` with tasks, dependencies, and duration estimates
- **Step 2 — Execution (optional):** If `execution_mode=plan_and_execute`, tasks run in dependency order via the TaskExecutor

**Input schema (`TaskPlanInput`):**
```python
goal: str                           # High-level objective
context: Optional[str]              # Research output to inform the plan
constraints: Optional[List[str]]    # Time/resource limits
execution_mode: ExecutionMode       # plan_only | plan_and_execute
max_tasks: Optional[int]            # Cap number of tasks (default: 10)
```

**Output schema (`TaskPlanOutput`):**
```python
plan: List[Task]                    # Ordered tasks with IDs and dependencies
execution_results: List[TaskResult] # Results if executed
status_summary: StatusSummary       # total / completed / failed / pending
next_action: Optional[str]          # Suggested next step
blockers: List[str]                 # Skipped tasks and reasons
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key — [platform.openai.com](https://platform.openai.com)
- Tavily API key — [tavily.com](https://tavily.com)

---

### 1. Clone the repository

```bash
git clone https://github.com/Sumayya-Jabeen/agentic-ai-platform.git
cd agentic-ai-platform
```

---

### 2. Backend setup

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Frontend setup

```bash
cd frontend
npm install
```

---

## Environment Variables

Create a `.env` file in the **project root**:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
API_SECRET_KEY=your_chosen_secret_key_here
```

Create a `.env.local` file inside the **`frontend/`** folder:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your_chosen_secret_key_here
```

> `API_SECRET_KEY` and `NEXT_PUBLIC_API_KEY` must be the same value — this is how the frontend authenticates with the backend.

---

## Running the Platform

### Start the backend

```bash
uvicorn api.main:app --reload --port 8000
```

- Backend API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

### Start the frontend

```bash
cd frontend
npm run dev
```

- Frontend: `http://localhost:3000`

---

## API Reference

All endpoints except `/health` require the `X-API-Key` header.

```
X-API-Key: your_chosen_secret_key_here
```

---

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — no auth required |
| `POST` | `/chat` | Send a message, receive full response |
| `POST` | `/chat/stream` | Send a message, receive SSE token stream |

**POST /chat/stream — Request body:**
```json
{
  "message": "Research the best Python web frameworks",
  "session_id": "optional-existing-session-id"
}
```

**SSE Event types:**
```
{ "type": "session", "session_id": "abc123" }
{ "type": "token",   "content": "Here " }
{ "type": "done" }
{ "type": "error",   "message": "..." }
```

---

### Sessions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions` | List all sessions |
| `GET` | `/history/{session_id}` | Get full message history |
| `DELETE` | `/history/{session_id}` | Clear a session |
| `PATCH` | `/sessions/{session_id}/rename` | Rename a session |

**PATCH /sessions/{session_id}/rename — Request body:**
```json
{ "title": "My renamed conversation" }
```

---

### Skills (direct endpoints)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/research` | Invoke Research Skill directly |
| `POST` | `/plan` | Invoke Task Planning Skill directly |

**POST /research — Request body:**
```json
{
  "query": "Latest advancements in large language models",
  "focus_areas": ["fine-tuning", "inference speed"],
  "output_format": "structured"
}
```

**POST /plan — Request body:**
```json
{
  "goal": "Launch a SaaS product in 3 months",
  "constraints": ["budget under $5000", "team of 2"],
  "execution_mode": "plan_only",
  "max_tasks": 8
}
```

---

## Frontend Features

| Feature | Description |
|---|---|
| Token-by-token streaming | Response appears word by word as the AI generates it |
| Markdown rendering | Full Markdown with bold, italic, headers, and lists |
| Code syntax highlighting | Code blocks with copy button and language detection |
| Dark / Light mode | Toggle in the header, persisted in localStorage |
| Voice input | Speak your message using the browser microphone |
| Session history | All conversations listed in the sidebar |
| Search conversations | Filter sessions by title or preview content |
| Pin conversations | Pin important sessions to the top of the sidebar |
| Rename conversations | Set a custom title for any session |
| Delete conversations | Remove a session from history |
| Export conversation | Download the full chat as a Markdown file |
| Browser notifications | Get notified when a response finishes in a background tab |
| Message editing | Edit any sent message and resend from that point |
| Regenerate response | Re-run the AI on any previous message |
| Feedback buttons | Thumbs up / down on any AI response |

---

## Contributors

| Contributor | Role |
|---|---|
| **Sumayya Jabeen** | Backend — FastAPI, Orchestrator, Skills, Tools, API routes, Middleware, Documentation |
| **Hurmath Jabeen** | Frontend — Next.js, Components, Hooks, Streaming, UI/UX, Testing (pytest) |
