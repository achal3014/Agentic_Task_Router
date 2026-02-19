from app.graph import build_graph


def test_translate_flow_end_to_end():
    graph = build_graph()

    state = {
        "user_input": "Translate this to English: Hola",
        "task_type": "",
        "reasoning": "",
        "response": "",
        "error": None,
        "safety_flag": False
    }

    result = graph.invoke(state)

    assert result["task_type"] == "translate"
    assert result["response"]
    assert result["error"] is None
