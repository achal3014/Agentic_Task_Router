"""
LangGraph workflow orchestration for the document assistant system.

This module defines the state machine that routes user requests through safety checks,
task routing, and specialized agents (summarizer, QnA, translator).
"""

import os
from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.agents.router_agent import route_task
from app.agents.summarizer_agent import summarize_text
from app.agents.qna_agent import answer_question
from app.agents.translator_agent import translate_text
from app.safety.safety import safety_check
from app.safety.suspicion_check import suspicion_check
from app.llm import LLMServiceError
from app.configs import ENABLE_TIER2
# Read from environment - NO import yet
GUARDRAILS_ENABLED = ENABLE_TIER2


def safety_node(state: AgentState) -> AgentState:
    """
    Performs Tier-1 safety checks on user input.

    Blocks requests containing medical advice, legal advice, financial advice,
    or other restricted topics based on keyword matching.

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with safety_flag set if blocked, or suspicion_flag if suspicious
    """
    result = safety_check(state["user_input"])

    if result["blocked"]:
        state["safety_flag"] = True
        state["safety_reason"] = result["reason"]
        state["response"] = "Request blocked due to safety restrictions."
        state["error"] = "Blocked by Tier-1 safety rules."
        state["suspicion_flag"] = False
        return state

    state["safety_flag"] = False
    state["safety_reason"] = None
    state["suspicion_flag"] = suspicion_check(state["user_input"])

    return state


def router_node(state: AgentState) -> AgentState:
    """
    Routes user request to appropriate specialized agent.

    Uses an LLM to classify the request into one of:
    - summarize: Text summarization
    - qna: Question answering based on document
    - translate: Language translation to English
    - unsupported: Invalid or unsupported request

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with task_type and routing_reasoning
    """
    try:
        router_output = route_task(state["user_input"])

        state["task_type"] = router_output.task_type
        state["routing_reasoning"] = router_output.reasoning

        if router_output.task_type not in ["summarize", "qna", "translate"]:
            state["task_type"] = "unsupported"

        state["error"] = None

    except LLMServiceError as e:
        state["task_type"] = "unsupported"
        state["routing_reasoning"] = "Router failed due to LLM error."
        state["error"] = str(e)

    return state


def summarizer_node(state: AgentState) -> AgentState:
    """
    Generates concise summaries of provided text.

    Uses an LLM to create clear, beginner-friendly summaries focusing on
    main ideas and key points without adding interpretations.

    Optionally validates output through guardrails if GUARDRAILS_ENABLED=true.

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with response, tokens_used, and model_used
    """
    try:
        content, tokens, model = summarize_text(state["user_input"])

        if GUARDRAILS_ENABLED:
            # Import only when needed
            from app.guardrails.output_guard import validate_output

            guard = validate_output(content)
            if not guard["allowed"]:
                state["response"] = "Response blocked due to output safety policy."
                state["error"] = guard["reason"]
                state["tokens_used"] = tokens
                state["model_used"] = model
                return state

        state["response"] = content
        state["tokens_used"] = tokens
        state["model_used"] = model
        state["error"] = None

    except LLMServiceError as e:
        state["response"] = "Service temporarily unavailable. Please try again."
        state["tokens_used"] = None
        state["model_used"] = None
        state["error"] = str(e)

    return state


def qna_node(state: AgentState) -> AgentState:
    """
    Answers questions based strictly on provided documentation.

    Uses an LLM to answer questions using ONLY the provided document,
    without adding external knowledge or making recommendations.

    Optionally validates output through guardrails if GUARDRAILS_ENABLED=true.

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with response, tokens_used, and model_used
    """
    try:
        content, tokens, model = answer_question(state["user_input"])

        if GUARDRAILS_ENABLED:
            # Import only when needed
            from app.guardrails.output_guard import validate_output

            guard = validate_output(content)
            if not guard["allowed"]:
                state["response"] = "Response blocked due to output safety policy."
                state["error"] = guard["reason"]
                state["tokens_used"] = tokens
                state["model_used"] = model
                return state

        state["response"] = content
        state["tokens_used"] = tokens
        state["model_used"] = model
        state["error"] = None

    except LLMServiceError as e:
        state["response"] = "Service temporarily unavailable. Please try again."
        state["tokens_used"] = None
        state["model_used"] = None
        state["error"] = str(e)

    return state


def translator_node(state: AgentState) -> AgentState:
    """
    Translates text from any language to English.

    Uses an LLM to perform mechanical translation while preserving meaning,
    tone, and structure. Only outputs English translations.

    Optionally validates output through guardrails if GUARDRAILS_ENABLED=true.

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with response, tokens_used, and model_used
    """
    try:
        content, tokens, model = translate_text(state["user_input"])

        if GUARDRAILS_ENABLED:
            # Import only when needed
            from app.guardrails.output_guard import validate_output

            guard = validate_output(content)
            if not guard["allowed"]:
                state["response"] = "Response blocked due to output safety policy."
                state["error"] = guard["reason"]
                state["tokens_used"] = tokens
                state["model_used"] = model
                return state

        state["response"] = content
        state["tokens_used"] = tokens
        state["model_used"] = model
        state["error"] = None

    except LLMServiceError as e:
        state["response"] = "Service temporarily unavailable. Please try again."
        state["tokens_used"] = None
        state["model_used"] = None
        state["error"] = str(e)

    return state


def fallback_node(state: AgentState) -> AgentState:
    """
    Handles unsupported requests and error cases.

    Provides appropriate error messages for:
    - Safety-blocked requests
    - Unsupported task types
    - Unexpected errors

    Args:
        state: Current agent state

    Returns:
        Updated state with appropriate error response
    """
    if state.get("safety_flag"):
        state["response"] = "Request blocked due to safety restrictions."
        state["error"] = state.get("error") or "Blocked by safety policy."
        return state

    if state.get("task_type") == "unsupported":
        state["response"] = state.get(
            "response") or "This task is not supported by the system."
        state["error"] = state.get("error") or "Unsupported task."
        return state

    state["response"] = "An unexpected error occurred."
    state["error"] = "Fallback triggered due to unknown routing."
    return state


def build_graph():
    """
    Constructs and compiles the LangGraph state machine workflow.

    Defines the complete execution graph:
    1. safety → Check input safety
    2. router → Classify task type
    3. [summarizer|qna|translator] → Execute specialized agent
    4. fallback → Handle errors/unsupported

    Returns:
        Compiled LangGraph workflow ready for execution
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("safety", safety_node)
    workflow.add_node("router", router_node)
    workflow.add_node("summarizer", summarizer_node)
    workflow.add_node("qna", qna_node)
    workflow.add_node("translator", translator_node)
    workflow.add_node("fallback", fallback_node)

    workflow.set_entry_point("safety")

    workflow.add_conditional_edges(
        "safety",
        lambda state: "blocked" if state.get("safety_flag") else "safe",
        {
            "blocked": "fallback",
            "safe": "router"
        }
    )

    workflow.add_conditional_edges(
        "router",
        lambda state: state["task_type"],
        {
            "summarize": "summarizer",
            "qna": "qna",
            "translate": "translator",
            "unsupported": "fallback"
        }
    )

    workflow.add_edge("summarizer", END)
    workflow.add_edge("qna", END)
    workflow.add_edge("translator", END)
    workflow.add_edge("fallback", END)

    return workflow.compile()
