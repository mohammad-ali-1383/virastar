"""Tests for the Gemini-backed correction service and its end-to-end wiring.

The provider is wired to ``httpx.MockTransport`` and injected through the same
FastAPI dependency the app uses, so the real HTTP layer, validation, and error
handlers are exercised without a real API key or network access.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import (
    INTERNAL_ERROR,
    PROVIDER_AUTH_ERROR,
    PROVIDER_RATE_LIMIT,
    PROVIDER_TIMEOUT,
    PROVIDER_UNAVAILABLE,
    ProviderUnavailableError,
)
from app.main import app
from app.services.correction import GeminiCorrectionService, get_correction_service
from app.services.gemini import GeminiProvider
from app.services.prompt import PERSIAN_PROOFREADING_SYSTEM_PROMPT

CORRECT_URL = "/api/v1/correct"
MODEL = "gemini-3.8-flash"
BASE_URL = "https://generativelanguage.googleapis.com"
API_KEY = "integration-test-key-not-real"
PERSIAN_TEXT = "سلام این یک متن ازمایشی است"

Handler = Callable[[httpx.Request], httpx.Response]


def _success_body(text: str) -> dict[str, object]:
    return {"candidates": [{"content": {"role": "model", "parts": [{"text": text}]}}]}


def _provider(handler: Handler) -> GeminiProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GeminiProvider(
        api_key=API_KEY,
        model=MODEL,
        base_url=BASE_URL,
        timeout_seconds=5.0,
        client=client,
    )


# --- Service behaviour ------------------------------------------------------


class _RecordingProvider(GeminiProvider):
    """Provider double that records the arguments and returns a fixed value."""

    def __init__(self, result: str = "corrected", error: Exception | None = None) -> None:
        super().__init__(api_key=API_KEY, model=MODEL)
        self._result = result
        self._error = error
        self.calls: list[tuple[str, str]] = []

    async def generate(self, *, system_instruction: str, user_text: str) -> str:
        self.calls.append((system_instruction, user_text))
        if self._error is not None:
            raise self._error
        return self._result


def test_service_sends_the_prompt_and_user_text_separately() -> None:
    provider = _RecordingProvider(result="متن اصلاحشده")
    service = GeminiCorrectionService(provider)

    result = asyncio.run(service.correct(PERSIAN_TEXT))

    assert result == "متن اصلاحشده"
    assert provider.calls == [(PERSIAN_PROOFREADING_SYSTEM_PROMPT, PERSIAN_TEXT)]


def test_service_propagates_provider_errors() -> None:
    provider = _RecordingProvider(error=ProviderUnavailableError("down"))
    service = GeminiCorrectionService(provider)

    with pytest.raises(ProviderUnavailableError):
        asyncio.run(service.correct(PERSIAN_TEXT))


def test_dependency_builds_a_gemini_backed_service() -> None:
    service = get_correction_service()

    assert isinstance(service, GeminiCorrectionService)


def test_provider_is_configured_from_settings() -> None:
    settings = Settings(
        _env_file=None,
        gemini_api_key="from-env-key",
        gemini_model="gemini-3.6-flash",
        gemini_api_base_url="https://example.test",
        gemini_timeout_seconds=12.5,
    )

    provider = GeminiProvider.from_settings(settings)

    assert provider.endpoint == "https://example.test/v1beta/models/gemini-3.6-flash:generateContent"


# --- End-to-end through POST /api/v1/correct --------------------------------


@pytest.fixture
def client_factory() -> Iterator[Callable[[Handler], TestClient]]:
    """Yield a factory that returns a TestClient with a mock Gemini provider."""

    def factory(handler: Handler) -> TestClient:
        service = GeminiCorrectionService(_provider(handler))
        app.dependency_overrides[get_correction_service] = lambda: service
        return TestClient(app)

    try:
        yield factory
    finally:
        app.dependency_overrides.clear()


def test_endpoint_returns_the_provider_correction(
    client_factory: Callable[[Handler], TestClient],
) -> None:
    client = client_factory(lambda _: httpx.Response(200, json=_success_body("سلام، این یک متن آزمایشی است.")))

    response = client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 200
    assert response.json() == {"corrected_text": "سلام، این یک متن آزمایشی است."}


def test_endpoint_sends_the_correction_prompt(
    client_factory: Callable[[Handler], TestClient],
) -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_success_body("ok"))

    client_factory(handler).post(CORRECT_URL, json={"text": "متن"})

    body = json.loads(captured[0].content)
    assert body["systemInstruction"]["parts"][0]["text"] == PERSIAN_PROOFREADING_SYSTEM_PROMPT
    assert body["contents"][0]["parts"][0]["text"] == "متن"


@pytest.mark.parametrize(
    ("status_code", "expected_status", "expected_code"),
    [
        (401, 502, PROVIDER_AUTH_ERROR),
        (403, 502, PROVIDER_AUTH_ERROR),
        (429, 429, PROVIDER_RATE_LIMIT),
        (500, 503, PROVIDER_UNAVAILABLE),
        (503, 503, PROVIDER_UNAVAILABLE),
        (504, 504, PROVIDER_TIMEOUT),
    ],
)
def test_endpoint_maps_provider_failures_to_documented_errors(
    client_factory: Callable[[Handler], TestClient],
    status_code: int,
    expected_status: int,
    expected_code: str,
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": {"code": status_code, "status": "X"}})

    response = client_factory(handler).post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == expected_status
    body = response.json()
    assert body["error"] == expected_code
    assert "corrected_text" not in body


def test_endpoint_timeout_is_a_gateway_timeout(
    client_factory: Callable[[Handler], TestClient],
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    response = client_factory(handler).post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 504
    assert response.json()["error"] == PROVIDER_TIMEOUT


def test_endpoint_empty_provider_output_is_not_a_success(
    client_factory: Callable[[Handler], TestClient],
) -> None:
    client = client_factory(lambda _: httpx.Response(200, json={"candidates": []}))

    response = client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 500
    assert response.json()["error"] == INTERNAL_ERROR
    assert "corrected_text" not in response.json()


def test_endpoint_never_leaks_provider_detail_or_credentials(
    client_factory: Callable[[Handler], TestClient],
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={
                "error": {
                    "code": 503,
                    "status": "UNAVAILABLE",
                    "message": f"backend overloaded for key {API_KEY}",
                }
            },
        )

    response = client_factory(handler).post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 503
    assert response.json()["error"] == PROVIDER_UNAVAILABLE
    assert API_KEY not in response.text
    assert "backend overloaded" not in response.text
