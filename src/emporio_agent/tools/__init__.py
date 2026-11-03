"""Typed tools the agent can call (decision D08)."""


class ToolError(ValueError):
    """Invalid tool input. The message is returned to the model, never a stack trace."""
