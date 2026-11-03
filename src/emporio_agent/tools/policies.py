"""Policy lookup tool (decisions D02/D03)."""

from __future__ import annotations

from emporio_agent.data.loader import normalize
from emporio_agent.policies import PolicyTopic, load_policy
from emporio_agent.tools import ToolError


def get_store_policy(topic: str) -> dict:
    try:
        policy_topic = PolicyTopic(normalize(str(topic)))
    except ValueError as exc:
        valid = ", ".join(t.value for t in PolicyTopic)
        raise ToolError(f"tema inválido; use um de: {valid}") from exc
    return {"tema": policy_topic.value, "politica": load_policy(policy_topic)}
