"""LLM providers."""

from __future__ import annotations

from emporio_agent.config import Settings
from emporio_agent.llm.base import LLMError, LLMProvider


def create_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "gemini":
        from emporio_agent.llm.gemini import GeminiProvider

        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.llm_model)
    raise LLMError(f"Provedor não suportado: {settings.llm_provider}")
