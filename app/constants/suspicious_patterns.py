SUSPICIOUS_PATTERNS = [
    # ----------------
    # Advice Seeking
    # ----------------
    "what should i do",
    "should i",
    "recommend",
    "which one is better",
    "what would you do",

    # ----------------
    # Prompt Injection / Jailbreak
    # ----------------
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous",
    "new instructions",
    "act as",
    "you are now",
    "pretend you are",
    "developer mode",
    "jailbreak",

    # ----------------
    # System Prompt Extraction
    # ----------------
    "show me your prompt",
    "what are your instructions",
    "reveal your prompt",
    "output your instructions",

    # ----------------
    # Multi-Task Chaining
    # ----------------
    "and then",
    "also do",
    "in addition",
    "followed by",

    # ----------------
    # Opinion / Fact-Checking Requests
    # ----------------
    "is this correct",
    "verify this",
    "fact check",

    # ----------------
    # Hypothetical Harm Wrapper
    # ----------------
    "hypothetically",
    "just for research",
    "theoretical question",
]
