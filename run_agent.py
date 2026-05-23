"""Azure AI Foundry entrypoint.

Foundry's "On Conversation Start" trigger should set:
    SURVEY_ID, WORKSPACE_ID, CATEGORY
This script reads them, validates, and runs a single co-pilot session.
"""
from __future__ import annotations

import json
import logging
import os
import sys

from mangrove_copilot.models import TriggerPayload
from mangrove_copilot.session import run_session


def _read_trigger() -> TriggerPayload:
    survey_id = os.environ.get("SURVEY_ID")
    workspace_id = os.environ.get("WORKSPACE_ID")
    category = os.environ.get("CATEGORY")
    # The user's JWT, forwarded by the Foundry "On Conversation Start"
    # trigger from the frontend session. Per-conversation, never stored.
    auth_token = os.environ.get("USER_TOKEN")
    missing = [
        name
        for name, value in (
            ("SURVEY_ID", survey_id),
            ("WORKSPACE_ID", workspace_id),
            ("CATEGORY", category),
        )
        if not value
    ]
    if missing:
        raise SystemExit(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )
    try:
        workspace_id_int = int(workspace_id)  # type: ignore[arg-type]
    except ValueError as exc:
        raise SystemExit(f"WORKSPACE_ID must be an integer: {exc}")
    return TriggerPayload(
        SurveyID=survey_id,  # type: ignore[arg-type]
        WorkspaceID=workspace_id_int,
        Category=category,  # type: ignore[arg-type]
        AuthToken=auth_token,
    )


def main() -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    trigger = _read_trigger()
    session = run_session(trigger)
    audit_json = json.dumps(
        session.to_audit().model_dump(mode="json"), indent=2, default=str
    )
    print("\n--- Audit entry ---")
    print(audit_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
