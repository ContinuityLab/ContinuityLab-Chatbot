"""Top-level session orchestration: glue the trigger, repo, voice, and tree."""
from __future__ import annotations

from typing import Optional

from mangrove_copilot.agent import Voice, get_voice
from mangrove_copilot.console import Console, StdConsole
from mangrove_copilot.db.base import MangroveRepo
from mangrove_copilot.db.factory import get_repo
from mangrove_copilot.engine.router import get_tree
from mangrove_copilot.engine.state_machine import Session, run_tree
from mangrove_copilot.models import TriggerPayload
from mangrove_copilot.scoring import calculate_resilience_score


def run_session(
    trigger: TriggerPayload,
    *,
    repo: Optional[MangroveRepo] = None,
    console: Optional[Console] = None,
    voice: Optional[Voice] = None,
) -> Session:
    """Run a single co-pilot session end-to-end and return the final state.

    Any of `repo`, `console`, or `voice` may be supplied for testing; if
    omitted, defaults are sourced from the environment.
    """
    repo = repo or get_repo(auth_token=trigger.auth_token)
    console = console or StdConsole()
    voice = voice or get_voice()

    survey = repo.get_survey(trigger.survey_id, trigger.workspace_id)
    if survey.category != trigger.category:
        # Glass-box guardrail: Foundry passed a category that doesn't match
        # the survey record. Refuse rather than silently re-routing.
        raise ValueError(
            f"Category mismatch: trigger says {trigger.category!r} but survey "
            f"{trigger.survey_id} is {survey.category!r}."
        )

    session = Session(
        trigger=trigger,
        survey=survey,
        repo=repo,
        console=console,
        voice=voice,
        resilience_score=calculate_resilience_score(survey),
    )
    nodes = get_tree(trigger.category)
    return run_tree(session, nodes, start=1)
