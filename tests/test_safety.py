# tests/test_safety.py
from app.safety.safety import safety_check


def test_medical_block():
    result = safety_check("Can you diagnose my illness?")
    assert result["blocked"] is True
