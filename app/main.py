import time
from fastapi import FastAPI
from app.graph import build_graph
from app.models import APIRequest, APIResponse
from app.logger import log_decision
from app.configs import ENABLE_LOGGING
from fastapi.middleware.cors import CORSMiddleware
from app.session import get_or_create_session_id


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
        "session_id": get_or_create_session_id(request.session_id),
        "user_input": request.user_input,
        "task_type": "",
        "routing_reasoning": "",
        "response": "",
        "error": None,
        "safety_flag": False,
        "suspicion_flag": False,
        "safety_reason": None,
        "model_used": None,
        "tokens_used": None,
        "confidence": None,
        "escalation_confirmed": None,
        "escalation_offer": None,
        "conversation_history": None,
    }

    start_time = time.time()
    result = graph.invoke(initial_state)
    end_time = time.time()

    latency_ms = int((end_time - start_time) * 1000)

    if ENABLE_LOGGING:
        log_decision(result, latency_ms)

    return APIResponse(
        session_id=result.get("session_id"),
        task_type=result.get("task_type", "unsupported"),
        response=result.get("response", ""),
        reasoning=(
            result.get("routing_reasoning")
            or result.get("safety_reason")
            or "Request blocked by safety policy."
        ),
        confidence=result.get("confidence"),
        error=result.get("error"),
        safety_flag=result.get("safety_flag", False),
        suspicion_flag=result.get("suspicion_flag", False),
        escalation_offer=result.get("escalation_offer"),
        escalation_confirmed=result.get("escalation_confirmed"),
    )
