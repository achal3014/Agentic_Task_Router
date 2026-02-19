from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.agents.router_agent import route_task
from app.agents.summarizer_agent import summarize_text
from app.agents.qna_agent import answer_question
from app.agents.translator_agent import translate_text
from app.safety.safety import safety_check
from app.safety.suspicion_check import suspicion_check
from app.llm import LLMServiceError


# -------------------------
# Nodes
# -------------------------

def safety_node(state: AgentState) -> AgentState:
    result = safety_check(state["user_input"])

    # Tier-1 hard block
    if result["blocked"]:
        state["safety_flag"] = True
        state["safety_reason"] = result["reason"]
        state["response"] = "Request blocked due to safety restrictions."
        state["error"] = "Blocked by Tier-1 safety rules."
        state["suspicion_flag"] = False
        return state

    # Tier-2 soft suspicion
    state["safety_flag"] = False
    state["safety_reason"] = None
    state["suspicion_flag"] = suspicion_check(state["user_input"])

    return state


def router_node(state: AgentState) -> AgentState:
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
    try:
        content, tokens, model = summarize_text(state["user_input"])
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
    try:
        content, tokens, model = answer_question(state["user_input"])
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
    try:
        content, tokens, model = translate_text(
            state["user_input"])
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
    if state.get("safety_flag"):
        state["task_type"] = "unsupported"
        state["response"] = "Request blocked due to safety restrictions."
        state["error"] = "Blocked by Tier-1 safety rules."
        return state

    if state.get("task_type") == "unsupported":
        state["response"] = "This task is not supported by the system."
        state["error"] = "Unsupported task."
        return state

    state["task_type"] = "unsupported"
    state["response"] = "An unexpected error occurred."
    state["error"] = "Fallback triggered due to unknown routing."
    return state


# -------------------------
# Graph Builder
# -------------------------

def build_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("safety", safety_node)
    workflow.add_node("router", router_node)
    workflow.add_node("summarizer", summarizer_node)
    workflow.add_node("qna", qna_node)
    workflow.add_node("translator", translator_node)
    workflow.add_node("fallback", fallback_node)

    # Entry point
    workflow.set_entry_point("safety")

    # --------------------------------
    # Safety conditional routing
    # --------------------------------
    workflow.add_conditional_edges(
        "safety",
        lambda state: "blocked" if state.get("safety_flag") else "safe",
        {
            "blocked": "fallback",
            "safe": "router"
        }
    )

    # --------------------------------
    # Router conditional routing
    # --------------------------------
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

    # End after execution
    workflow.add_edge("summarizer", END)
    workflow.add_edge("qna", END)
    workflow.add_edge("translator", END)
    workflow.add_edge("fallback", END)

    return workflow.compile()
