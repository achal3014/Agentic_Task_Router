import time
import pprint
from app.graph import build_graph
from app.logger import log_decision


def run_test(user_input: str):
    graph = build_graph()

    initial_state = {
        "user_input": user_input,
        "task_type": "",
        "reasoning": "",
        "response": "",
        "error": None,
        "safety_flag": False
    }

    # Measure latency
    start_time = time.time()
    result = graph.invoke(initial_state)
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000

    # Log final decision
    log_decision(result, latency_ms)

    # Pretty print result
    print("\n===== FINAL STATE =====")
    pprint.pprint(result)

    print(f"\nLatency: {round(latency_ms, 2)} ms")
    print("=======================\n")


if __name__ == "__main__":
    # Change this input to test different scenarios

    # Example 1: Normal translation
    run_test("Urban green spaces play an important role in improving the quality of life in cities by providing areas for recreation, relaxation, and social interaction. Parks, gardens, and tree-lined streets help reduce air pollution, regulate temperature, and support local biodiversity. Beyond environmental benefits, these spaces also contribute to mental well-being by offering a break from the noise and stress of urban life. As cities continue to grow, thoughtful planning and preservation of green spaces are increasingly recognized as essential for creating healthier and more sustainable urban environments.")

    # Example 2: Safety block
    # run_test("What is the full form of LLM?")

    # Example 3: Unsupported task
    # run_test("Write a Python function to sort a list.")
