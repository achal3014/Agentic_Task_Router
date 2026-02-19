from app.prompts.system_policy import SYSTEM_POLICY


def build_prompt(agent_prompt: str, user_input: str) -> str:
    """
    Builds the final prompt by prepending the system-wide policy
    to the agent-specific prompt and user input.
    """
    return f"""
        {SYSTEM_POLICY}

        {agent_prompt}

        USER INPUT:
        {user_input}
    """
