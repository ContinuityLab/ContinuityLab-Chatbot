"""Repo factory: chooses ApiClientRepo when configured, StubRepo otherwise.

The bearer token is per-user and per-session; it must be supplied at call
time, not loaded from the environment.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from mangrove_copilot.db.base import MangroveRepo
from mangrove_copilot.db.stub import StubRepo

log = logging.getLogger(__name__)


def get_repo(auth_token: Optional[str] = None) -> MangroveRepo:
    base = os.environ.get("MANGROVE_API_BASE")
    if not base:
        log.info("MANGROVE_API_BASE not set; using in-memory StubRepo.")
        return StubRepo()
    if not auth_token:
        log.warning(
            "MANGROVE_API_BASE is set but no auth_token was supplied; "
            "falling back to StubRepo. Forward the user's JWT in the "
            "trigger payload to enable live API calls."
        )
        return StubRepo()

    # Imported lazily so the stub path doesn't require httpx at runtime.
    from mangrove_copilot.db.api_client import ApiClientRepo

    return ApiClientRepo(base_url=base, auth_token=auth_token)
