"""Tests for the auth-token / repo factory wiring."""
from __future__ import annotations

import pytest

from mangrove_copilot.db.factory import get_repo
from mangrove_copilot.db.stub import StubRepo


def test_factory_returns_stub_when_api_base_unset(monkeypatch):
    monkeypatch.delenv("MANGROVE_API_BASE", raising=False)
    repo = get_repo(auth_token="any-token")
    assert isinstance(repo, StubRepo)


def test_factory_falls_back_to_stub_when_no_token(monkeypatch):
    monkeypatch.setenv("MANGROVE_API_BASE", "https://example.invalid")
    repo = get_repo(auth_token=None)
    assert isinstance(repo, StubRepo)


def test_api_client_requires_token(monkeypatch):
    from mangrove_copilot.db.api_client import ApiClientRepo

    with pytest.raises(ValueError, match="auth_token"):
        ApiClientRepo(base_url="https://example.invalid", auth_token="")


def test_factory_builds_api_client_when_configured(monkeypatch):
    monkeypatch.setenv("MANGROVE_API_BASE", "https://example.invalid")
    from mangrove_copilot.db.api_client import ApiClientRepo

    repo = get_repo(auth_token="user-jwt")
    assert isinstance(repo, ApiClientRepo)
