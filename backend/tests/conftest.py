"""Shared fixtures for the backend test suite.

The correction service is replaced by a stub so routine tests never call an
external provider (`testing.md`, `coding-rules.md` → Testing).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.correction import get_correction_service


class StubCorrectionService:
    """Test double for :class:`~app.services.correction.CorrectionService`.

    Records the text it receives and either returns ``result`` or raises
    ``error``, which lets tests simulate both successful and failing providers.
    """

    def __init__(self, result: str | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.received: list[str] = []

    async def correct(self, text: str) -> str:
        self.received.append(text)

        if self.error is not None:
            raise self.error

        return self.result if self.result is not None else text


@pytest.fixture
def stub_service() -> StubCorrectionService:
    """Stub correction service injected into the app's dependencies."""
    return StubCorrectionService()


@pytest.fixture
def client(stub_service: StubCorrectionService) -> Iterator[TestClient]:
    """API client with the stub correction service wired in."""
    app.dependency_overrides[get_correction_service] = lambda: stub_service

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def tolerant_client(stub_service: StubCorrectionService) -> Iterator[TestClient]:
    """Client that returns error responses instead of re-raising server errors."""
    app.dependency_overrides[get_correction_service] = lambda: stub_service

    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
