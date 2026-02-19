# tests/test_fallback.py
from app.graph import build_graph


def test_unsupported_task_goes_to_fallback():
    graph = build_graph()

    state = {
        "user_input": "Write a Python web scraper",
        "task_type": "",
        "reasoning": "",
        "response": "",
        "error": None,
        "safety_flag": False
    }

    result = graph.invoke(state)

    assert result["task_type"] == "unsupported"
    assert "not supported" in result["response"].lower()
