"""Shared fixtures for the backend test suite.

Provider traffic is always mocked: the correction service is replaced by a stub
for API tests, and the real provider adapters are exercised through
``httpx.MockTransport`` so no external call is ever made
(`testing.md`, `coding-rules.md` -> Testing).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import settings
from app.main import app
from app.services.correction import get_correction_service

Handler = Callable[[httpx.Request], httpx.Response]

# Placeholder credentials for the mocked provider calls. They are not real keys
# and never leave the process.
GROQ_TEST_KEY = "test-groq-key-not-real"
GEMINI_TEST_KEY = "test-gemini-key-not-real"


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


class ProviderTransport:
    """Mock provider transport that records the requests the adapters send.

    Handlers are keyed by nothing: one handler answers every request, and the
    recorded ``requests`` list gives tests access to the URL, headers, and body
    the adapter actually produced.
    """

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self._handler: Handler = lambda _: httpx.Response(200, json={})

    def respond(self, handler: Handler) -> None:
        """Install the handler that answers subsequent provider requests."""
        self._handler = handler

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handler(request)


@pytest.fixture
def provider_transport(monkeypatch: pytest.MonkeyPatch) -> ProviderTransport:
    """Route provider HTTP through a mock transport (no network, no real key).

    The adapters build their own ``httpx.AsyncClient`` when a request is made,
    so patching the client class is what lets the real adapter code — endpoint,
    headers, payload, timeout, and error mapping — run without external calls.
    """
    transport = ProviderTransport()
    real_client = httpx.AsyncClient

    def patched(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs["transport"] = httpx.MockTransport(transport.handle)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", patched)

    return transport


@pytest.fixture
def provider_client(provider_transport: ProviderTransport) -> Iterator[TestClient]:
    """API client with the real provider wiring and mocked provider HTTP."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def provider_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give both providers placeholder keys without touching any real secret."""
    monkeypatch.setattr(settings, "groq_api_key", SecretStr(GROQ_TEST_KEY))
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr(GEMINI_TEST_KEY))
