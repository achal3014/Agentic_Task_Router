"""
Research Agent — deep knowledge retrieval with LangChain tools.

Invoked when user explicitly requests research or confirms QnA escalation.
Uses LangChain @tool definitions for schema but selects tools via JSON prompt.
Uses call_llm for all LLM calls — consistent with the rest of the system.

Tools available:
- wikipedia: factual encyclopedic knowledge
- web_search: current events and broad web results (optional, config-toggled)
- arxiv: academic papers and research publications
"""

import json
from app.llm import call_llm
from app.prompts.research_prompt import RESEARCH_PROMPT
from app.prompts.system_policy import SYSTEM_POLICY
from app.configs import (
    MAIN_MODEL,
    RESEARCH_TEMPERATURE,
    RESEARCH_MAX_TOKENS,
    HISTORY_TURNS,
    ENABLE_WEB_SEARCH,
)
from app.tools.wikipedia_tool import search_wikipedia
from app.tools.web_search_tool import search_web
from app.tools.arxiv_tool import search_arxiv


def _get_tools() -> list:
    """
    Returns the list of available tools based on config.
    Web search only included if ENABLE_WEB_SEARCH is true.
    ArXiv always included.
    """
    tools = [search_wikipedia, search_arxiv]
    if ENABLE_WEB_SEARCH:
        tools.append(search_web)
    return tools


def _select_tools_via_llm(
    user_input: str, available_tools: list
) -> tuple[list[str], int]:
    """
    Asks the LLM which tools to use via a simple JSON response.

    Args:
        user_input: The research query
        available_tools: List of LangChain tool objects

    Returns:
        Tuple of (list of tool name strings, tokens used)
    """
    tool_descriptions = "\n".join(
        f"- {t.name}: {t.description}" for t in available_tools
    )

    default_tool = available_tools[0].name if available_tools else "wikipedia"

    prompt = f"""You are a tool selection assistant. Given a research query, decide which tools to use.

Available tools:
{tool_descriptions}

Rules:
- Select one or more tools from the available tools list above
- Use wikipedia for factual questions about people, concepts, history, definitions
- Use search_arxiv for questions about latest research, scientific papers, AI advancements, technical topics, academic studies
- Use web_search for current events, trends, recent news, or latest non-academic information
- You may select multiple tools if the query benefits from multiple sources
- Return ONLY a JSON array of tool names from the available list, nothing else

Query: {user_input}

Response (JSON array only, e.g. ["{default_tool}"]):"""

    try:
        llm_response = call_llm(
            prompt=prompt,
            model=MAIN_MODEL,
            temperature=0,
            max_tokens=100,
        )
        raw = llm_response.get("content", "").strip()
        selection_tokens = llm_response.get("tokens_used") or 0

        if raw.startswith("```"):
            raw = raw.split("```")[1].replace("json", "").strip()

        tools = json.loads(raw)
        valid_names = [t.name for t in available_tools]
        selected = [t for t in tools if t in valid_names]

        if not selected:
            selected = valid_names
            print(
                f"[research] No valid tools selected — falling back to all available: {valid_names}"
            )

        return selected, selection_tokens

    except Exception as e:
        valid_names = [t.name for t in available_tools]
        print(
            f"[research] Tool selection failed: {str(e)} — using all available tools: {valid_names}"
        )
        return valid_names, 0


def run_research(state: dict) -> tuple[str, int | None, str, list]:
    """
    Executes the Research agent.

    Flow:
    1. Build context from state (escalation, history, retrieved context)
    2. call_llm selects tools via JSON prompt
    3. Tools executed manually
    4. call_llm synthesizes final answer with tool results

    Args:
        state: Full agent state

    Returns:
        Tuple of (response_text, tokens_used, model_used, tools_called)
    """
    user_input = state.get("user_input", "")
    history = state.get("conversation_history") or []
    prior_response = state.get("response", "")
    retrieved_context = state.get("retrieved_context", "")

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

    retrieved_context_block = ""
    if retrieved_context:
        retrieved_context_block = f"""
PRIOR CONTEXT FROM MEMORY:
{retrieved_context}
"""

    system_content = f"""
{SYSTEM_POLICY}

{RESEARCH_PROMPT}

{escalation_context}
{history_context}
{retrieved_context_block}

Now answer the below query:
"""

    tools = _get_tools()
    tool_map = {t.name: t for t in tools}

    print(f"[research] Available tools: {list(tool_map.keys())}")

    # Step 1 — Select tools via JSON prompt
    selected_tool_names, selection_tokens = _select_tools_via_llm(user_input, tools)
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

    full_prompt = f"{system_content}\n\n{synthesis_input}"

    result = call_llm(
        prompt=full_prompt,
        model=MAIN_MODEL,
        temperature=RESEARCH_TEMPERATURE,
        max_tokens=RESEARCH_MAX_TOKENS,
    )

    content = result["content"]
    synthesis_tokens = result.get("tokens_used") or 0

    total_tokens = selection_tokens + synthesis_tokens
    tokens_used = total_tokens if total_tokens > 0 else None

    return content, tokens_used, MAIN_MODEL, tools_called
