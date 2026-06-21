"""
Unit tests for the optional API-key authentication dependency.
"""
import asyncio

import pytest
from fastapi import HTTPException

from src.agent import verify_api_key


def _run(coro):
    return asyncio.run(coro)


def test_auth_disabled_when_env_unset(monkeypatch):
    monkeypatch.delenv("GUARDIAN_API_KEY", raising=False)
    # Any (or no) key is accepted when auth is disabled.
    assert _run(verify_api_key(x_api_key=None)) is None
    assert _run(verify_api_key(x_api_key="anything")) is None


def test_correct_key_accepted(monkeypatch):
    monkeypatch.setenv("GUARDIAN_API_KEY", "s3cret")
    assert _run(verify_api_key(x_api_key="s3cret")) is None


def test_wrong_key_rejected(monkeypatch):
    monkeypatch.setenv("GUARDIAN_API_KEY", "s3cret")
    with pytest.raises(HTTPException) as exc:
        _run(verify_api_key(x_api_key="wrong"))
    assert exc.value.status_code == 401


def test_missing_key_rejected_when_required(monkeypatch):
    monkeypatch.setenv("GUARDIAN_API_KEY", "s3cret")
    with pytest.raises(HTTPException) as exc:
        _run(verify_api_key(x_api_key=None))
    assert exc.value.status_code == 401
