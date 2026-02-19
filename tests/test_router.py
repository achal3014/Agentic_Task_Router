import pytest
from app.graph import build_graph

# This is your old evaluation dataset, now as test cases
ROUTING_TEST_CASES = [
    # --- Clear baseline ---
    ("Summarize this paragraph about AI.", "summarize"),
    ("Translate this to Spanish: AI is powerful.", "translate"),
    ("What is machine learning?", "qna"),
    ("Write a Python sorting function.", "unsupported"),
    ("Can you diagnose my medical condition?", "unsupported"),

    # --- Tricky: Question that actually asks for summary ---
    (
        "Can you give me a short summary of the following article on climate change?",
        "summarize"
    ),

    # --- Tricky: Looks like QnA but is translation ---
    (
        "What does this sentence mean in French: 'Knowledge is power'?",
        "translate"
    ),

    # --- Tricky: Long text + question at end (should still be summarize) ---
    (
        "Here is a long paragraph about neural networks. Can you summarize it briefly?",
        "summarize"
    ),

    # --- Tricky: Translation without explicit word 'translate' ---
    (
        "Convert the following sentence into German: Artificial intelligence is evolving rapidly.",
        "translate"
    ),

    # --- Tricky: QnA phrased indirectly ---
    (
        "I want to understand how backpropagation works in neural networks.",
        "qna"
    ),

    # --- Tricky: Multi-intent (router should pick dominant intent) ---
    (
        "Explain machine learning in simple terms and keep it short.",
        "qna"
    ),

    # --- Tricky: Summarization using synonyms ---
    (
        "Give me a brief overview of this document on cloud computing.",
        "summarize"
    ),

    # --- Tricky: Translation request hidden in polite language ---
    (
        "Could you please help me by putting this sentence into Hindi: Data is the new oil.",
        "translate"
    ),

    # --- Tricky: Looks harmless but should be unsupported (advice) ---
    (
        "What legal steps should I take if my contract is breached?",
        "unsupported"
    ),
]


@pytest.mark.parametrize("user_input, expected_task", ROUTING_TEST_CASES)
def test_routing_decision(user_input, expected_task):
    graph = build_graph()

    state = {
        "user_input": user_input,
        "task_type": "",
        "reasoning": "",
        "response": "",
        "error": None,
        "safety_flag": False
    }

    result = graph.invoke(state)

    assert result["task_type"] == expected_task
