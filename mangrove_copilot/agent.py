"""Azure AI Foundry voice wrapper.

The agent is read-only: it explains what the engine is doing, paraphrases
facts, and never controls branching. If the platform is not configured (no
endpoint env var), this falls back to a deterministic local voice that just
echoes the prompt verbatim — handy for tests and offline runs.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Protocol

log = logging.getLogger(__name__)


class Voice(Protocol):
    def say(self, prompt: str, *, context: Optional[str] = None) -> str: ...


class LocalVoice:
    """Echo voice. Returns the prompt unchanged. Always available."""

    def say(self, prompt: str, *, context: Optional[str] = None) -> str:
        return prompt


class FoundryVoice:
    """Voice that calls an Azure AI Foundry agent for a paraphrased response.

    Lazy-imports the Azure SDK so the rest of the engine works without it.
    """

    def __init__(
        self,
        endpoint: str,
        agent_name: str,
        agent_version: str,
    ) -> None:
        from azure.ai.projects import AIProjectClient  # type: ignore
        from azure.identity import DefaultAzureCredential  # type: ignore

        self._project = AIProjectClient(
            endpoint=endpoint, credential=DefaultAzureCredential()
        )
        self._client = self._project.get_openai_client()
        self._agent_ref = {"name": agent_name, "version": agent_version}

    def say(self, prompt: str, *, context: Optional[str] = None) -> str:
        instructions = prompt if context is None else f"{prompt}\n\nContext:\n{context}"
        try:
            response = self._client.responses.create(  # type: ignore[attr-defined]
                model="gpt-4o-mini",
                input=instructions,
                extra_body={"agent_reference": self._agent_ref},
            )
            return getattr(response, "output_text", None) or instructions
        except Exception as exc:  # pragma: no cover - network failure path
            log.warning("FoundryVoice failed (%s); falling back to literal prompt.", exc)
            return instructions


def get_voice() -> Voice:
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    name = os.environ.get("FOUNDRY_AGENT_NAME")
    version = os.environ.get("FOUNDRY_AGENT_VERSION")
    if endpoint and name and version:
        try:
            return FoundryVoice(endpoint=endpoint, agent_name=name, agent_version=version)
        except Exception as exc:
            log.warning("Could not initialize FoundryVoice (%s); using LocalVoice.", exc)
    return LocalVoice()
