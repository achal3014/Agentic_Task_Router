from guardrails.hub import ToxicLanguage, ProfanityFree, DetectJailbreak, DetectPII
from guardrails import Guard
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


# Test combined guard
guard = (
    Guard()
    .use(ToxicLanguage(threshold=0.3, validation_method="sentence"))
    .use(ProfanityFree())
    .use(DetectJailbreak())
    .use(DetectPII(pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD"]))
)

test_text = "These people are fucking idiots"
print(f"Testing: {test_text}\n")

result = guard.validate(test_text)

print(f"validation_passed: {result.validation_passed}")
print(f"validated_output: {result.validated_output}")
print(f"error: {result.error}")
print(f"\nvalidation_summaries: {result.validation_summaries}")

if result.validation_summaries:
    for i, summary in enumerate(result.validation_summaries):
        print(f"\n--- Summary {i+1} ---")
        print(f"Type: {type(summary)}")
        print(f"Dir: {dir(summary)}")
        print(f"Summary: {summary}")
