from app.guardrails.output_guard import validate_output, get_guardrails_status
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


TEST_CASES = [
    {
        "name": "Safe output",
        "input": "Artificial intelligence improves efficiency in many industries.",
        "should_block": False
    },
    {
        "name": "Profanity - fuck",
        "input": "This is fucking terrible work.",
        "should_block": True
    },
    {
        "name": "Profanity - shit",
        "input": "What a piece of shit.",
        "should_block": True
    },
    {
        "name": "Profanity - multiple",
        "input": "These fucking idiots don't know shit.",
        "should_block": True
    },
    {
        "name": "PII - Email",
        "input": "Contact me at john.doe@example.com for more information.",
        "should_block": True
    },
    {
        "name": "PII - Phone",
        "input": "Call me at 555-123-4567 if you need help.",
        "should_block": True
    },
    {
        "name": "PII - Credit Card",
        "input": "My card number is 4532-1234-5678-9010.",
        "should_block": True
    },
    {
        "name": "PII - Multiple",
        "input": "Email: test@test.com, Phone: 555-0000",
        "should_block": True
    },
    {
        "name": "Technical content",
        "input": "The function returns a boolean value indicating success or failure.",
        "should_block": False
    },
    {
        "name": "Neutral paraphrase",
        "input": "The text expresses criticism of individuals and their work.",
        "should_block": False
    },
    {
        "name": "Business language",
        "input": "Please review the attached document and provide feedback by EOD.",
        "should_block": False
    },
    {
        "name": "Borderline profanity (clean)",
        "input": "This situation is really annoying and frustrating.",
        "should_block": False
    }
]


def run_tests():
    status = get_guardrails_status()

    print("=" * 80)
    print("GUARDRAILS OUTPUT VALIDATION TESTS")
    print("=" * 80)
    print(f"Guardrails Enabled: {status['enabled']}")
    print(
        f"Active Validators: {', '.join(status['validators']) if status['validators'] else 'None'}")
    print("=" * 80)
    print()

    if not status['enabled']:
        print("⚠️  WARNING: Guardrails are DISABLED")
        print("Set GUARDRAILS_ENABLED=true in your .env file to enable validation")
        print()

    passed = 0
    failed = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"Test {i}/{len(TEST_CASES)}: {test['name']}")
        print(f"Input: {test['input']}")

        result = validate_output(test['input'])
        blocked = not result["allowed"]

        print(f"Result: {'BLOCKED' if blocked else 'ALLOWED'}")
        if blocked:
            print(f"Reason: {result['reason']}")

        print(f"Expected: {'BLOCKED' if test['should_block'] else 'ALLOWED'}")

        if blocked == test['should_block']:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            failed += 1

        print("-" * 80)

    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(TEST_CASES)}")
    print(f"Passed: {passed} ({passed/len(TEST_CASES)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(TEST_CASES)*100:.1f}%)")
    print("=" * 80)

    if status['enabled']:
        print("\n💡 Tip: Set GUARDRAILS_ENABLED=false to disable validation")
    else:
        print("\n💡 Tip: Set GUARDRAILS_ENABLED=true to enable validation")

    return passed == len(TEST_CASES)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
