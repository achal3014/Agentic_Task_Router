import time
from fastapi import FastAPI
from app.graph import build_graph
from app.models import APIRequest, APIResponse
from app.logger import log_decision
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Agentic Task Router")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


@app.post("/route", response_model=APIResponse)
def route_request(request: APIRequest):
    initial_state = {
        "user_input": request.user_input,
        "task_type": "",
        "reasoning": "",
        "response": "",
        "error": None,
        "safety_flag": False
    }

    start_time = time.time()
    result = graph.invoke(initial_state)
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000

    # Log final decision
    log_decision(result, latency_ms)

    return APIResponse(
        task_type=result.get("task_type", "unsupported"),
        response=result.get("response", ""),
        reasoning=(
            result.get("routing_reasoning")
            or result.get("safety_reason")
            or "Request blocked by safety policy."
        ),
        error=result.get("error"),
        safety_flag=result.get("safety_flag", False),        # ← Add this
        suspicion_flag=result.get("suspicion_flag", False)   # ← Add this
    )
