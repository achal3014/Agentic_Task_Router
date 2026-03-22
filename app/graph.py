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
from app.agents.research_agent import run_research
from app.safety.safety import safety_check
from app.safety.suspicion_check import suspicion_check
from app.cost.tracker import accumulate_cost, calculate_cost
from app.llm import LLMServiceError
from app.configs import ENABLE_TIER2, ENABLE_MEMORY, ROUTER_MODEL

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


def memory_read_node(state: AgentState) -> AgentState:
    """
    Reads conversation history from Redis for this session.
    Skipped if ENABLE_MEMORY is false.
    """
    if not ENABLE_MEMORY:
        state["conversation_history"] = []
        state["retrieved_context"] = ""
        return state

    session_id = state.get("session_id")
    if not session_id:
        state["conversation_history"] = []
        state["retrieved_context"] = ""
        return state

    # Short-term — Redis
    from app.memory.redis_store import (
        read_history,
    )  # Heavy imports so defined inside function

    history = read_history(session_id)
    state["conversation_history"] = history
    print(f"[memory] Read {len(history)} turns for session {session_id}")

    # Long-term — ChromaDB
    from app.memory.vector_store import (
        retrieve_context,
    )  # Heavy imports so defined inside function

    user_input = state.get("user_input", "")
    context = retrieve_context(user_input)
    state["retrieved_context"] = context
    if context:
        print(f"[memory] Retrieved prior context ({len(context)} chars)")

    return state


def router_node(state: AgentState) -> AgentState:
    """
    Routes user request to appropriate specialized agent.

    Uses an LLM to classify the request into one of:
    - summarize: Text summarization
    - qna: Question answering based on document
    - translate: Language translation to English
    - research: Answers open-ended knowledge questions
    - unsupported: Invalid or unsupported request

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with task_type and routing_reasoning
    """
    try:
        router_output, router_tokens = route_task(state)

        state["task_type"] = router_output.task_type
        state["routing_reasoning"] = router_output.reasoning
        state["confidence"] = router_output.confidence

        state["cost_usd"] = accumulate_cost(
            state.get("cost_usd"), calculate_cost(ROUTER_MODEL, router_tokens)
        )

        if router_output.task_type not in ["summarize", "qna", "translate", "research"]:
            state["task_type"] = "unsupported"

        state["error"] = None

    except LLMServiceError as e:
        state["task_type"] = "unsupported"
        state["routing_reasoning"] = "Router failed due to LLM error."
        state["error"] = str(e)
    return state


def confidence_gate_node(state: AgentState) -> AgentState:
    """
    Blocks low-confidence routing decisions.
    If confidence is below threshold, returns a clarification
    request instead of routing to an agent.
    """
    from app.configs import MIN_CONFIDENCE_THRESHOLD

    confidence = state.get("confidence") or 1.0

    if confidence < MIN_CONFIDENCE_THRESHOLD:
        state["task_type"] = "unsupported"
        state["response"] = (
            "I wasn't confident enough to classify your request. "
            "Could you please rephrase or provide more detail?"
        )
        state["error"] = "Low confidence routing — clarification needed."
    print(
        "confidence gate node - confidence after confidence_gate_node content exec:",
        state.get("confidence"),
    )

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
        content, tokens, model = summarize_text(state)

        state["cost_usd"] = accumulate_cost(
            state.get("cost_usd"), calculate_cost(model, tokens)
        )

        if GUARDRAILS_ENABLED:
            # Import only when needed
            from app.guardrails.output_guard import (
                validate_output,
            )  # Heavy imports so defined inside function

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
    Answer questions using either the provided document or its general training knowledge.

    Uses an LLM to answer questions without making any recommendations.

    Optionally validates output through guardrails if GUARDRAILS_ENABLED=true.

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with response, tokens_used, and model_used
    """
    try:
        content, tokens, model = answer_question(state)

        state["cost_usd"] = accumulate_cost(
            state.get("cost_usd"), calculate_cost(model, tokens)
        )

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

    state["escalation_offer"] = True

    print("QNA NODE - escalation_offer being set to:", state.get("escalation_offer"))
    print("QNA NODE - full state keys:", list(state.keys()))

    return state


def escalation_check_node(state: AgentState) -> AgentState:
    """
    Checks if the user confirmed escalation to the Research agent.
    Looks for affirmative responses to the QnA escalation offer.
    """
    print(
        "ESCALATION CHECK NODE - escalation_offer in state:",
        state.get("escalation_offer"),
    )
    print("ESCALATION CHECK NODE - full state:", dict(state))
    user_input = state.get("user_input", "").lower().strip()

    AFFIRMATIVES = [
        "yes",
        "yeah",
        "yep",
        "sure",
        "go ahead",
        "please",
        "yes please",
        "do it",
        "go for it",
        "deeper",
        "more",
        "in-depth",
        "research it",
    ]

    confirmed = any(phrase in user_input for phrase in AFFIRMATIVES)
    state["escalation_confirmed"] = confirmed
    return state


def translator_node(state: AgentState) -> AgentState:
    """
    Translates text from any language to any language

    Uses an LLM to perform mechanical translation while preserving meaning,
    tone, and structure.

    Optionally validates output through guardrails if GUARDRAILS_ENABLED=true.

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with response, tokens_used, and model_used
    """
    try:
        content, tokens, model = translate_text(state["user_input"])

        state["cost_usd"] = accumulate_cost(
            state.get("cost_usd"), calculate_cost(model, tokens)
        )

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


def research_node(state: AgentState) -> AgentState:
    """
    Handles open-ended knowledge questions using training knowledge. For deep analysis tasks
    choose research agent instead of QnA agent. Tools will be added in a later feature.
    Takes care of any queries which are asking explicitly for research over any topic

    Args:
        state: Current agent state containing user_input

    Returns:
        Updated state with response, tokens_used, and model_used
    """
    try:
        content, tokens, model, tools = run_research(state)

        state["cost_usd"] = accumulate_cost(
            state.get("cost_usd"), calculate_cost(model, tokens)
        )

        if GUARDRAILS_ENABLED:
            from app.guardrails.output_guard import validate_output

            guard = validate_output(content)
            if not guard["allowed"]:
                state["response"] = "Response blocked due to output safety policy."
                state["error"] = guard["reason"]
                state["tokens_used"] = tokens
                state["model_used"] = model
                state["tools_called"] = tools
                return state

        state["task_type"] = "research"
        state["response"] = content
        state["tokens_used"] = tokens
        state["model_used"] = model
        state["tools_called"] = tools
        state["error"] = None

    except LLMServiceError as e:
        state["response"] = "Service temporarily unavailable. Please try again."
        state["tokens_used"] = None
        state["model_used"] = None
        state["tools_called"] = None
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
        state["response"] = (
            state.get("response") or "This task is not supported by the system."
        )
        state["error"] = state.get("error") or "Unsupported task."
        return state

    state["response"] = "An unexpected error occurred."
    state["error"] = "Fallback triggered due to unknown routing."
    return state


def memory_write_node(state: AgentState) -> AgentState:
    """
    Writes the current turn to Redis after agent execution.
    Skipped if ENABLE_MEMORY is false or response is empty.
    Skipped for safety-blocked or unsupported responses.
    """
    if not ENABLE_MEMORY:
        return state

    session_id = state.get("session_id")
    if not session_id:
        return state

    if state.get("safety_flag") or state.get("task_type") == "unsupported":
        return state

    response = state.get("response", "").strip()
    user_input = state.get("user_input", "").strip()
    task_type = state.get("task_type", "")
    error = state.get("error")

    # Redis — always write turn
    from app.memory.redis_store import (
        write_turn,
    )  # Heavy imports so defined inside function

    if user_input:
        write_turn(session_id, "user", user_input)
    if response:
        write_turn(session_id, "assistant", response)
    print(f"[memory] Wrote turn for session {session_id}")

    # ChromaDB — only write meaningful outputs
    from app.memory.manager import should_store_in_vector
    from app.memory.vector_store import store_output

    if should_store_in_vector(task_type, response, error):
        store_output(session_id, task_type, user_input, response)
        print(f"[memory] Stored {task_type} output in vector store")

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
    workflow.add_node("memory_read", memory_read_node)
    workflow.add_node("router", router_node)
    workflow.add_node("confidence_gate", confidence_gate_node)
    workflow.add_node("summarizer", summarizer_node)
    workflow.add_node("qna", qna_node)
    workflow.add_node("escalation_check", escalation_check_node)
    workflow.add_node("translator", translator_node)
    workflow.add_node("research", research_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("memory_write", memory_write_node)

    workflow.set_entry_point("safety")

    workflow.add_conditional_edges(
        "safety",
        lambda state: "blocked" if state.get("safety_flag") else "safe",
        {"blocked": "fallback", "safe": "memory_read"},
    )

    workflow.add_edge("memory_read", "router")
    workflow.add_edge("router", "confidence_gate")

    workflow.add_conditional_edges(
        "confidence_gate",
        lambda state: state["task_type"],
        {
            "summarize": "summarizer",
            "qna": "qna",
            "translate": "translator",
            "research": "research",
            "unsupported": "fallback",
        },
    )

    workflow.add_edge("summarizer", "memory_write")
    workflow.add_edge("qna", "escalation_check")
    workflow.add_conditional_edges(
        "escalation_check",
        lambda state: (
            "research" if state.get("escalation_confirmed") else "memory_write"
        ),
        {"research": "research", "memory_write": "memory_write"},
    )
    workflow.add_edge("translator", "memory_write")
    workflow.add_edge("research", "memory_write")
    workflow.add_edge("memory_write", END)
    workflow.add_edge("fallback", END)

    return workflow.compile()
