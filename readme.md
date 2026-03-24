# Knowva — General Purpose Knowledge Assistant

A production-grade multi-agent knowledge assistant that intelligently routes user requests to specialized agents using **LangGraph**, **FastAPI**, **Groq LLMs**, and **LangChain Tools** — with persistent memory, semantic retrieval, tool-augmented research, structured safety enforcement, and full observability.

---

## Problem Statement

Traditional LLM applications rely on a single prompt to handle all user interactions:

- No task specialization — a generalist model handles every request regardless of complexity
- No memory — every conversation starts from scratch with no prior context
- No tool access — agents cannot retrieve external or academic information
- No cost governance — all queries consume the same high-capability model
- Safety delegated entirely to model self-regulation with no independent enforcement
- No observability — failures are opaque with no traceable root cause

---

## Solution Overview

Knowva implements a **stateful, collaborative, tool-using agentic platform** — a structured coordination layer between the user and the underlying models. Every request is classified, enriched with memory, dispatched to the appropriate specialist agent, and optionally escalated for deeper research.

- Intent classified by a lightweight router with confidence scoring
- Short-term memory (Redis) maintains conversation context per session
- Long-term memory (ChromaDB) retrieves semantically relevant prior outputs
- Specialized agents handle execution with models appropriate to the task
- Research agent uses LangChain tools (Wikipedia, ArXiv, Web Search) for deep answers
- QnA agent offers human-in-the-loop escalation to Research when needed
- Safety enforced structurally at both input and output stages
- Every decision logged with cost, latency, and tool usage

---

## Architecture

### Request Flow

```
User Request
    → Tier-1 Safety Filter
    → Memory Read (Redis + ChromaDB)
    → Router Agent (Intent Classification + Confidence Gate)
    → Specialized Agent Execution
        ├── Summarizer
        ├── QnA (with escalation offer)
        ├── Translator
        └── Research (Wikipedia + ArXiv + Web Search tools)
    → Memory Write (Redis + ChromaDB)
    → Output Guardrails
    → Response + Decision Log
```

### Agent Collaboration Flow

QnA Agent → answers question → offers escalation
    ↓ user confirms
Research Agent → selects tools → fetches results → synthesizes answer

Memory Write Node (centralized)
    ├── Redis → store raw conversation turns (short-term)
    └── Summarizer Agent → compress entire conversation
            ↓
        Vector Store (Chroma) → store summary as long-term memory

### Research Agent Tool Flow

```
Research Agent
    → Tool Selection (LLM-based JSON selection)
    → Execute selected tools in parallel
        ├── Wikipedia (factual/encyclopedic)
        ├── ArXiv (academic papers, 5 results — relevance + recency merged)
        └── Web Search / DuckDuckGo (current events, optional)
    → Synthesize tool results + training knowledge
    → Return comprehensive answer
```

---

## Agents

| Agent | Responsibility |
|---|---|
| Router Agent | Classifies intent via lightweight LLM with confidence scoring |
| Summarizer Agent | Condenses text or uploaded documents; no external knowledge |
| QnA Agent | Answers questions from document or training knowledge; offers research escalation |
| Translator Agent | Faithful translation to/from any language |
| Research Agent | Deep knowledge retrieval using Wikipedia, ArXiv, and web search tools |

---

## Tech Stack

| Component | Technology |
|---|---|
| API Layer | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Provider | Groq |
| LLM Tools | LangChain + LangChain-Groq |
| Short-Term Memory | Redis |
| Long-Term Memory | ChromaDB + Sentence Transformers |
| Research Tools | Wikipedia, ArXiv, DuckDuckGo (ddgs) |
| Document Reading | PyMuPDF (fitz) |
| Structured Validation | Pydantic |
| Retry & Fallback | Tenacity |
| Output Validation | Guardrails AI |
| Frontend | Streamlit |
| Audit Trail | JSONL Logging |

---

## Memory Architecture

### Short-Term Memory — Redis
- Stores conversation history per session (last N turns, configurable)
- TTL-based expiry — sessions auto-clear after configured duration
- Used by router for context-aware routing (e.g. understanding "yes please" as escalation)
- Used by research agent to build on prior conversation

### Long-Term Memory — ChromaDB
- Stores summarized agent outputs as semantic embeddings
- Cross-session retrieval — prior knowledge surfaces in new conversations
- Deduplication — near-duplicate entries replaced, not appended
- Topic change detection — irrelevant context skipped automatically
- Outputs summarized before storage to keep vector store lean

---

## Safety & Guardrails

### Layer 1 — Input Safety (Hard Block)
- Keyword-based blocking for restricted domains: medical, legal, financial
- PII detection at entry point
- Jailbreak attempt detection
- LLM-level semantic suspicion check as secondary filter

### Layer 2 — Output Safety
- Guardrails AI screens every response before delivery
- Blocks profanity, PII leakage, and unsafe content

**Design Principle:** Each layer operates independently. Any uncertain input defaults to refusal — never a guess.

---

## Project Structure

```
app/
├── agents/
│   ├── router_agent.py        # Intent classification with confidence scoring
│   ├── summarizer_agent.py    # Text summarization
│   ├── qna_agent.py           # Open-ended + document QnA with escalation
│   ├── translator_agent.py    # Multi-language translation
│   └── research_agent.py      # Tool-augmented deep research
├── memory/
│   ├── redis_store.py         # Short-term session memory
│   ├── vector_store.py        # Long-term semantic memory (ChromaDB)
│   └── manager.py             # Memory write coordination
├── tools/
│   ├── wikipedia_tool.py      # Wikipedia search (LangChain @tool)
│   ├── arxiv_tool.py          # ArXiv paper search (LangChain @tool)
│   ├── web_search_tool.py     # DuckDuckGo web search (LangChain @tool)
│   └── document_reader.py     # PDF/TXT text extraction (PyMuPDF)
├── cost/
│   └── tracker.py             # Per-call token and USD cost tracking
├── safety/                    # Tier-1 input safety checks
├── guardrails/                # Tier-2 output validation
├── prompts/                   # All prompt templates
├── graph.py                   # LangGraph workflow definition
├── llm.py                     # LLM wrapper with fallback, retry, cost tracking
├── logger.py                  # Structured JSONL logging
├── models.py                  # Pydantic request/response models
├── state.py                   # AgentState definition
├── session.py                 # Session ID generation and validation
├── main.py                    # FastAPI entrypoint
frontend/
└── app.py                     # Streamlit UI (Knowva)
scripts/
├── eval_cases.py              # 56 hand-crafted evaluation cases
├── evaluate_agents.py         # Evaluation runner
└── compute_metrics.py         # Metrics computation
logs/
vector_store/                  # ChromaDB persistence
configs.ini                    # All configuration (models, memory, costs, tools)
```

---

## Getting Started

### 1. Prerequisites

- Redis running locally (`redis-server` or via GitHub Windows installer)
- Python 3.11+
- Groq API key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

Copy and edit `configs.ini`:

```ini
[LLM]
MAIN_MODEL = llama-3.3-70b-versatile
FALLBACK_MODEL = llama-3.1-8b-instant
ROUTER_MODEL = llama-3.1-8b-instant

[MEMORY]
ENABLE_MEMORY = true
REDIS_HOST = localhost
REDIS_PORT = 6379

[TOOLS]
ENABLE_WEB_SEARCH = true
```

Set your Groq API key in a `.env` file:

```env
GROQ_API_KEY=your_key_here
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

### 5. Start the Frontend

```bash
streamlit run frontend/app.py
```

### 6. Send a Request (API)

```bash
POST http://127.0.0.1:8000/route

{
  "user_input": "Research the latest developments in transformer architecture",
  "session_id": "optional-existing-session-id",
  "document": "optional-pre-extracted-document-text"
}
```

---

## Configuration Reference

| Section | Key | Description |
|---|---|---|
| `[LLM]` | `MAIN_MODEL` | Primary agent model |
| `[LLM]` | `ROUTER_MODEL` | Lightweight router model |
| `[LLM]` | `RESEARCH_MAX_TOKENS` | Max tokens for research synthesis |
| `[MEMORY]` | `ENABLE_MEMORY` | Toggle Redis + ChromaDB |
| `[MEMORY]` | `REDIS_TTL_SECONDS` | Session expiry duration |
| `[MEMORY]` | `HISTORY_TURNS` | Turns to read from Redis |
| `[MEMORY]` | `SIMILARITY_THRESHOLD` | ChromaDB deduplication threshold |
| `[MEMORY]` | `TOPIC_CHANGE_THRESHOLD` | Skip retrieval if topic changed |
| `[TOOLS]` | `ENABLE_WEB_SEARCH` | Toggle DuckDuckGo web search |
| `[COST]` | `COST_PER_1K_TOKENS_MAIN` | USD cost per 1K tokens (main model) |
| `[ROUTING]` | `MIN_CONFIDENCE_THRESHOLD` | Below this → clarification response |
| `[SAFETY]` | `ENABLE_TIER2` | Toggle Guardrails AI output check |
| `[LOGGING]` | `ENABLE_LOGGING` | Toggle JSONL decision logging |

---

## Evaluation & Performance

Evaluated across **56 hand-crafted test cases** covering normal inputs, edge cases, adversarial prompts, escalation flows, and memory cross-session retrieval.

| Metric | Result |
|---|---|
| Routing Accuracy | ~91% |
| Task Completion Rate | ~98% |
| API Success Rate | 100% |
| Avg Cost Per Query | ~$0.003 |

### Metrics Computed

- **Routing Accuracy** — correct agent selected vs expected
- **Task Completion Rate** — valid structured response returned end to end
- **Cost Per Query** — USD cost tracked per agent type
- **Memory Hit Rate** — requests that retrieved prior context from ChromaDB
- **Latency Per Agent** — average response time per task type (requires `ENABLE_LOGGING=true`)
- **Tool Usage Rate** — frequency of each research tool per research request

### Run Evaluation

```bash
# Run all 56 cases
python scripts/evaluate_agents.py

# Compute metrics
python scripts/compute_metrics.py
```

---

## Notable Engineering Decisions

- **Two-Model Strategy** — Lightweight `llama-3.1-8b-instant` for routing and tool selection; `llama-3.3-70b-versatile` reserved for agent synthesis. Cost-aware by design — expensive model only used when complexity justifies it.

- **LangChain Tool Pattern without Native Tool Calling** — Tools defined with `@tool` decorator for schema and description, but selected via a JSON prompt rather than Groq's native tool calling API, which produced malformed function calls. LLM selects tools by name, Python executes them manually — reliable and model-agnostic.

- **Two-Tier Memory Architecture** — Redis stores raw conversation turns (short-term, session-scoped, TTL-based). ChromaDB stores summarized agent outputs as semantic embeddings (long-term, cross-session). This separation ensures fast recency lookup from Redis and noise-free semantic retrieval from ChromaDB.

- **Summarization Before Vector Storage** — Agent responses are summarized by the Summarizer agent before being embedded into ChromaDB. This keeps the vector store lean and signal-rich rather than cluttered with verbose LLM outputs.

- **Memory-Informed Routing** — Router reads Redis conversation history before classifying intent. Follow-up messages like "yes please" are correctly understood as escalation confirmations rather than unsupported requests.

- **Human-in-the-Loop Escalation** — QnA agent always offers escalation to Research at the end of every response. User explicitly confirms before the Research agent is invoked — no automatic rerouting without consent. Escalation button rendered in the Streamlit frontend.

- **Confidence Gate** — Router returns a confidence score (0.0–1.0) with every classification. Requests below the configured threshold (`MIN_CONFIDENCE_THRESHOLD`) are returned with a clarification message instead of being routed to an agent. Prevents confidently wrong routing.

- **Two-Stage Suspicion Check** — Input safety uses keyword matching (Stage 1, instant) followed by an LLM semantic check (Stage 2) for implicit threats that keywords miss. Falls back to non-suspicious on Stage 2 failure — soft flag never blocks on its own.

- **Deduplication in Vector Store** — Before storing, ChromaDB is queried for near-duplicates (similarity > 0.95). Existing entry replaced rather than appended. Topic change detection skips retrieval entirely when current query is semantically unrelated to stored content.

- **Document Guard** — If a document is uploaded, Research routing is blocked at the router node level regardless of keywords used. Document queries always route to QnA (if a question is present) or Summarizer (if plain text). Prevents tool-fetching agents from ignoring the provided document.

- **Document Upload Support** — Frontend accepts PDF and TXT uploads. Text extracted via PyMuPDF (fitz) in the browser layer, sent as the `document` field in the API payload. Document text injected into `user_input` before graph execution — no agent code changes required.

- **Token Tracking Across All Agents** — Every LLM call returns `tokens_used` through the `call_llm` wrapper. Cost calculated per call using model-specific pricing from `configs.ini`. Cost accumulated across all agent nodes in a single request — router cost + agent cost + research tool selection cost all summed.

- **Configurable Safety Pipeline** — Output guardrails (Tier-2) toggled independently via `configs.ini` without affecting Tier-1 input safety. Each layer operates independently — bypassing one does not compromise the other.

- **Explicit Fallback Semantics** — Every failure path (LLM error, safety block, low confidence, unsupported task) has a defined, predictable outcome. No unhandled exceptions surface to the user. Tenacity handles transient LLM failures with exponential backoff before falling back to the secondary model.

- **ArXiv Integration with Hybrid Sorting** — ArXiv tool fetches papers sorted by both relevance and recency, merges and deduplicates results, returns top 5 abstracts. Ensures answers about latest research include both the most cited and most recent papers.

- **Session Identity** — Every request generates or reuses a UUID session ID. Returned in every response so the client can persist it for follow-up requests. Frontend stores it in Streamlit session state automatically — users never manage it manually.

---

## What This Project Demonstrates

This is not a simple LLM wrapper. It is a governed, stateful, tool-using agentic system built with production-grade patterns:

- **Specialization** — right agent for every task
- **Memory** — conversations that build on prior knowledge
- **Tool use** — real external information via Wikipedia, ArXiv, and web search
- **Collaboration** — QnA and Research agents working together with human confirmation
- **Safety** — two independent layers that cannot be bypassed together
- **Observability** — every decision logged with cost, latency, and tool usage
- **Reliability** — retry, fallback, confidence gating, and graceful error handling throughout