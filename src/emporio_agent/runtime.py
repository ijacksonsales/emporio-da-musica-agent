"""Wire settings, data, provider and stores into a ready-to-use agent."""

from __future__ import annotations

from dataclasses import dataclass

from emporio_agent.agent import Agent, AgentReply
from emporio_agent.config import Settings, get_settings
from emporio_agent.data.loader import load_store
from emporio_agent.llm import create_provider
from emporio_agent.memory import ConversationStore
from emporio_agent.tools.handoff import HandoffStore


@dataclass
class Runtime:
    settings: Settings
    agent: Agent
    memory: ConversationStore

    def chat(self, session_id: str, user_message: str) -> AgentReply:
        """Answer one message, persisting user and assistant text (not tool results)."""
        history = self.memory.load_history(session_id)
        reply = self.agent.respond(session_id, history, user_message)
        if not reply.error:
            self.memory.append(session_id, "user", user_message)
            self.memory.append(session_id, "assistant", reply.text)
        return reply


def build_runtime(settings: Settings | None = None) -> Runtime:
    settings = settings or get_settings()
    agent = Agent(
        provider=create_provider(settings),
        store=load_store(settings.data_dir),
        today=settings.reference_date,
        handoffs=HandoffStore(settings.db_path),
    )
    memory = ConversationStore(settings.db_path, ttl_days=settings.history_ttl_days)
    return Runtime(settings, agent, memory)
