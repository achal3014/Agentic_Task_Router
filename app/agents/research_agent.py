"""
Research Agent — deep knowledge retrieval with LangChain tools.

Invoked when user explicitly requests research or confirms QnA escalation.
Uses LangChain @tool definitions for schema but selects tools via JSON prompt
to avoid Groq's unreliable native tool calling API.
Synthesizes tool results with training knowledge for comprehensive answers.
"""

import os
import json
from app.prompts.research_prompt import RESEARCH_PROMPT
from app.prompts.system_policy import SYSTEM_POLICY
from app.configs import (
    MAIN_MODEL,
    RESEARCH_TEMPERATURE,
    RESEARCH_MAX_TOKENS,
    HISTORY_TURNS,
    ENABLE_WEB_SEARCH,
)
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.tools.wikipedia_tool import search_wikipedia
from app.tools.web_search_tool import search_web
from app.tools.vector_search_tool import search_vector_store


def _get_tools() -> list:
    """
    Returns the list of available tools based on config.
    Web search only included if ENABLE_WEB_SEARCH is true.
    """
    tools = [search_vector_store, search_wikipedia]
    if ENABLE_WEB_SEARCH:
        tools.append(search_web)
    return tools


def _select_tools_via_llm(
    user_input: str, available_tools: list, llm
) -> tuple[list[str], int]:
    """
    Asks the LLM which tools to use via a simple JSON response.
    Avoids Groq's native tool calling API which is unreliable for this model.

    Args:
        user_input: The research query
        available_tools: List of LangChain tool objects
        llm: LangChain LLM instance

    Returns:
        Tuple of (list of tool name strings, tokens used)
    """
    tool_descriptions = "\n".join(
        f"- {t.name}: {t.description}" for t in available_tools
    )

    prompt = f"""You are a tool selection assistant. Given a research query, decide which tools to use.

Available tools:
{tool_descriptions}

Rules:
- Always include vector_search
- Include wikipedia for factual questions about people, concepts, history, science
- Include web_search for current events, trends, recent news, or latest information
- Return ONLY a JSON array of tool names, nothing else

Query: {user_input}

Response (JSON array only, e.g. ["vector_search", "wikipedia"]):"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # Capture selection tokens
        selection_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            selection_tokens = response.usage_metadata.get("total_tokens", 0)

        if raw.startswith("```"):
            raw = raw.split("```")[1].replace("json", "").strip()

        tools = json.loads(raw)
        valid_names = [t.name for t in available_tools]
        selected = [t for t in tools if t in valid_names]

        # Always ensure vector_search is included
        if "vector_search" not in selected:
            selected.insert(0, "vector_search")

        return selected, selection_tokens

    except Exception as e:
        print(
            f"[research] Tool selection failed: {str(e)} — defaulting to vector_search"
        )
        return ["vector_search"], 0


def run_research(state: dict) -> tuple[str, int | None, str, list]:
    """
    Executes the Research agent.

    Flow:
    1. Build context from state (escalation, history)
    2. LLM selects tools via JSON prompt
    3. Tools executed manually
    4. LLM synthesizes final answer with tool results

    Args:
        state: Full agent state

    Returns:
        Tuple of (response_text, tokens_used, model_used, tools_called)
    """
    user_input = state.get("user_input", "")
    history = state.get("conversation_history") or []
    prior_response = state.get("response", "")

    # Build escalation context
    escalation_context = ""
    if state.get("escalation_confirmed") and prior_response:
        escalation_context = f"""
The user previously received this answer and requested deeper research:

PRIOR ANSWER:
{prior_response}

Build on this — do not repeat it. Go deeper and add new information.
"""

    # Build conversation history context
    history_context = ""
    if history:
        recent = history[-HISTORY_TURNS:]
        lines = "\n".join(f"{t['role'].upper()}: {t['content'][:300]}" for t in recent)
        history_context = f"""
Recent conversation:
{lines}
"""

    # Build system message
    system_content = f"""
{SYSTEM_POLICY}

{RESEARCH_PROMPT}

{escalation_context}
{history_context}
"""

    tools = _get_tools()
    tool_map = {t.name: t for t in tools}

    # LLM for tool selection — low tokens, zero temperature
    selection_llm = ChatGroq(
        model=MAIN_MODEL,
        temperature=0,
        max_tokens=100,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    # LLM for final synthesis
    synthesis_llm = ChatGroq(
        model=MAIN_MODEL,
        temperature=RESEARCH_TEMPERATURE,
        max_tokens=RESEARCH_MAX_TOKENS,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    # Step 1 — Select tools via JSON prompt
    selected_tool_names, selection_tokens = _select_tools_via_llm(
        user_input, tools, selection_llm
    )
    print(f"[research] Selected tools: {selected_tool_names}")

    # Step 2 — Execute selected tools
    tool_results = []
    tools_called = []

    for tool_name in selected_tool_names:
        tool_fn = tool_map.get(tool_name)
        if not tool_fn:
            continue
        try:
            result = tool_fn.invoke({"query": user_input})
            tool_results.append(f"[{tool_name}]: {result}")
            tools_called.append(tool_name)
            print(f"[research] Tool '{tool_name}' returned {len(str(result))} chars")
        except Exception as e:
            print(f"[research] Tool '{tool_name}' failed: {str(e)}")

    # Step 3 — Synthesize final answer
    if tool_results:
        tool_context = (
            "\n\nTOOL RESULTS (use these to enrich your answer):\n"
            + "\n\n".join(tool_results)
        )
        synthesis_input = f"{user_input}\n\n{tool_context}"
    else:
        synthesis_input = user_input

    final_messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=synthesis_input),
    ]

    final_response = synthesis_llm.invoke(final_messages)
    content = final_response.content

    # Extract synthesis tokens
    synthesis_tokens = 0
    if hasattr(final_response, "usage_metadata") and final_response.usage_metadata:
        synthesis_tokens = final_response.usage_metadata.get("total_tokens", 0)

    # Sum both selection and synthesis tokens
    total_tokens = (selection_tokens or 0) + (synthesis_tokens or 0)
    tokens_used = total_tokens if total_tokens > 0 else None

    return content, tokens_used, MAIN_MODEL, tools_called
