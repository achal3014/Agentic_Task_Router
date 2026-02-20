# Agentic Task Router with Safety & Guardrails

A modular, production-grade document assistant that intelligently routes user requests to specialized agents using **LangGraph**, **FastAPI**, and **Groq LLMs** — with structured safety enforcement, fallback resilience, and full decision logging.

---

## Problem Statement

Traditional LLM applications rely on a single prompt to handle all user interactions — an approach that introduces significant structural risk:

- No task specialization — a generalist model handles every request regardless of complexity
- No cost governance — all queries consume the same high-capability model
- Safety delegated entirely to model self-regulation with no independent enforcement
- No observability — failures are opaque with no traceable root cause

---

## Solution Overview

This project implements an **Agentic Task Router** — a structured coordination layer between the user and the underlying models. Every request is classified, validated, and dispatched to the appropriate specialist agent before any execution begins.

- Intent is classified by a lightweight router before any heavy processing occurs
- Specialized agents handle execution with models appropriate to the task
- Safety is enforced structurally at both input and output stages
- Every decision is logged for audit and evaluation

---

## Architecture

### Request Flow

```
User Request
    → Tier-1 Safety Filter
    → Router Agent (Intent Classification)
    → Specialized Agent Execution
    → Output Guardrails
    → Response + Decision Log
```

### Agents

| Agent | Responsibility |
|---|---|
| Router Agent | Classifies intent via lightweight LLM; returns strict JSON |
| Summarizer Agent | Condenses document text; no external knowledge used |
| Q&A Agent | Answers questions grounded strictly in provided document context |
| Translator Agent | Produces faithful translations; no interpretation or commentary |

---

## Tech Stack

| Component | Technology |
|---|---|
| API Layer | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Provider | Groq |
| Structured Validation | Pydantic |
| Retry & Fallback | Tenacity |
| Output Validation | Guardrails AI |
| Testing | Pytest |
| Audit Trail | JSONL Logging |

---

## Safety & Guardrails

### Layer 1 — Input Safety (Hard Block)

- Keyword-based blocking for restricted domains: medical, legal, financial
- Profanity and PII detection at the entry point
- Jailbreak attempt detection — adversarial prompt patterns flagged and rejected
- LLM-level instruction reinforcement as a secondary filter

### Layer 2 — Output Safety

- Guardrails AI screens every response before delivery
- Blocks profanity, PII leakage, and unsafe content
- Nothing leaves the pipeline unchecked

**Design Principle:** Each layer operates independently. Bypassing one does not compromise the other. Any uncertain input defaults to refusal — never a guess.

---

## Resilience & Reliability

- Exponential backoff retries via Tenacity for transient LLM failures
- Automatic failover to a secondary Groq model if the primary is unavailable
- Graceful fallback node ensures a valid structured response is always returned
- No unhandled exceptions surface to the user

---

## Project Structure

```
app/
├── agents/              # Router, Summarizer, Q&A, Translator
├── safety/              # Tier-1 & Tier-2 safety checks
├── guardrails/          # Output validation
├── prompts/             # Prompt templates
├── graph.py             # LangGraph workflow definition
├── llm.py               # LLM wrapper with fallback and retry logic
├── logger.py            # Structured JSONL logging
├── models.py            # Pydantic models
├── state.py             # AgentState definition
├── main.py              # FastAPI entrypoint
tests/
scripts/
├── evaluate_agents.py
├── compute_metrics.py
logs/
```

---

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```env
GROQ_API_KEY=your_key
GROQ_MAIN_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
GROQ_ROUTER_MODEL=llama-3.1-8b-instant
```

### 3. Start the API

```bash
uvicorn app.main:app --reload
```

### 4. Send a Request

```bash
POST http://127.0.0.1:8000/route

{
  "user_input": "Summarize the following document: ..."
}
```

---

## Evaluation & Performance

Evaluated across 40+ hand-crafted test cases covering normal inputs, edge cases, and adversarial prompts.

| Metric | Result |
|---|---|
| Routing Accuracy | ~95% |
| Task Completion Rate | ~100% |

**Routing Accuracy** measures whether the router correctly identified intent and dispatched to the appropriate agent.  
**Task Completion Rate** measures whether the pipeline returned a valid, structured response end to end.

---

## Notable Engineering Decisions

- **Cost-Aware Model Selection** — Lightweight LLM at the router; high-capability model reserved for agent execution
- **Configurable Safety Pipeline** — Output guardrails can be toggled independently without affecting input safety
- **Explicit Fallback Semantics** — Every failure path has a defined, predictable outcome with no silent degradation
- **FastAPI Middleware** — Safety checks and request logging enforced globally at the middleware layer, not duplicated per route

---

## Future Scope

- Native document ingestion — PDF, TXT, and DOCX support via a pre-processing extraction layer
- Session-level memory to persist document context across interactions
- Per-agent output guardrails for tighter task-level scope enforcement
- Confidence scoring on router decisions to enable human-in-the-loop review
- Prompt engineering to improve summarization depth and conceptual coverage

---

## What This Project Demonstrates

This is not a simple LLM wrapper. It is a governed agentic system built with production-grade patterns — designed for specialization, safety, auditability, and reliability from the ground up.