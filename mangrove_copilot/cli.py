"""Local CLI entry point: `python -m mangrove_copilot ...`."""
from __future__ import annotations

import argparse
import json
import sys

from mangrove_copilot.models import TriggerPayload
from mangrove_copilot.session import run_session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Mangrove decision-tree co-pilot locally."
    )
    parser.add_argument("--survey-id", required=True)
    parser.add_argument("--workspace-id", required=True, type=int)
    parser.add_argument(
        "--category", required=True, choices=["Redundancy", "Dependency"]
    )
    parser.add_argument(
        "--token",
        default=None,
        help="User bearer token. Without it, the engine uses the in-memory stub repo.",
    )
    args = parser.parse_args(argv)

    trigger = TriggerPayload(
        SurveyID=args.survey_id,
        WorkspaceID=args.workspace_id,
        Category=args.category,
        AuthToken=args.token,
    )
    session = run_session(trigger)
    print("\n--- Audit entry ---")
    print(json.dumps(session.to_audit().model_dump(mode="json"), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
