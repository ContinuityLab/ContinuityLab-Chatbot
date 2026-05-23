"""Shared test fixtures."""
from __future__ import annotations

from typing import Iterable

import pytest

from mangrove_copilot.agent import LocalVoice
from mangrove_copilot.console import ScriptedConsole
from mangrove_copilot.db.stub import StubRepo
from mangrove_copilot.models import TriggerPayload
from mangrove_copilot.session import run_session


@pytest.fixture
def repo() -> StubRepo:
    return StubRepo()


def run_with_script(
    repo: StubRepo,
    *,
    survey_id: str,
    workspace_id: int,
    category: str,
    answers: Iterable[str],
):
    console = ScriptedConsole(answers)
    trigger = TriggerPayload(
        SurveyID=survey_id, WorkspaceID=workspace_id, Category=category
    )
    session = run_session(trigger, repo=repo, console=console, voice=LocalVoice())
    return session, console
