"""Repo factory: chooses ApiClientRepo when configured, StubRepo otherwise."""
from __future__ import annotations

import logging
import os

from mangrove_copilot.db.base import MangroveRepo
from mangrove_copilot.db.stub import StubRepo

log = logging.getLogger(__name__)


def get_repo() -> MangroveRepo:
    base = os.environ.get("MANGROVE_API_BASE")
    if not base:
        log.info("MANGROVE_API_BASE not set; using in-memory StubRepo.")
        return StubRepo()

    # Imported lazily so the stub path doesn't require httpx at runtime.
    from mangrove_copilot.db.api_client import ApiClientRepo

    return ApiClientRepo(base_url=base)
