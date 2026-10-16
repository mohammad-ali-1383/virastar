"""Tests for the correction service and its end-to-end wiring.

Both selectable providers are exercised through ``httpx.MockTransport``
(installed by the ``provider_transport`` fixture) and reached through the same
FastAPI dependency the app uses, so the real HTTP layer, validation, prompt
handling, and error handlers are covered without a real API key or network
access.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.errors import (
    INTERNAL_ERROR,
    PROVIDER_AUTH_ERROR,
    PROVIDER_RATE_LIMIT,
    PROVIDER_TIMEOUT,
    PROVIDER_UNAVAILABLE,
    ProviderUnavailableError,
)
from app.services.correction import (
    GEMINI_PROVIDER,
    GROQ_PROVIDER,
    LLMCorrectionService,
    get_correction_service,
)
from app.services.prompt import PERSIAN_PROOFREADING_SYSTEM_PROMPT
from tests.conftest import GEMINI_TEST_KEY, GROQ_TEST_KEY, ProviderTransport

CORRECT_URL = "/api/v1/correct"
PERSIAN_TEXT = "سلام این یک متن ازمایشی است"
CORRECTED_TEXT = "سلام، این یک متن آزمایشی است."

DEFINED_PROVIDERS = [GROQ_PROVIDER, GEMINI_PROVIDER]

BodyBuilder = Callable[[str], dict[str, object]]
ErrorBuilder = Callable[[int], dict[str, object]]


def _groq_body(text: str) -> dict[str, object]:
    return {
        "id": "chatcmpl-test",
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}
        ],
    }


def _gemini_body(text: str) -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {"role": "model", "parts": [{"text": text}]},
                "finishReason": "STOP",
                "index": 0,
            }
        ]
    }


def _groq_error_body(status_code: int) -> dict[str, object]:
    return {"error": {"message": "provider detail", "type": "server_error", "code": status_code}}


def _gemini_error_body(status_code: int) -> dict[str, object]:
    return {"error": {"code": status_code, "message": "provider detail", "status": "UNAVAILABLE"}}


def _builders(provider: str) -> tuple[BodyBuilder, ErrorBuilder]:
    """Response builders for the provider under test."""
    if provider == GROQ_PROVIDER:
        return _groq_body, _groq_error_body
    return _gemini_body, _gemini_error_body


def _api_key_for(provider: str) -> str:
    return GROQ_TEST_KEY if provider == GROQ_PROVIDER else GEMINI_TEST_KEY


def _error_body_echoing(provider: str, message: str) -> dict[str, object]:
    """A provider error body whose free-form message echoes request material."""
    if provider == GROQ_PROVIDER:
        return {"error": {"message": message, "type": "server_error", "code": 503}}
    return {"error": {"code": 503, "message": message, "status": "UNAVAILABLE"}}


# --- Service behaviour ------------------------------------------------------


class _RecordingProvider:
    """Provider double that records the arguments and returns a fixed value."""

    def __init__(self, result: str = "corrected", error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[str, str]] = []

    async def generate(self, *, system_instruction: str, user_text: str) -> str:
        self.calls.append((system_instruction, user_text))
        if self._error is not None:
            raise self._error
        return self._result


def test_service_sends_the_prompt_and_user_text_separately() -> None:
    provider = _RecordingProvider(result="متن اصلاح‌شده")
    service = LLMCorrectionService(provider)

    result = asyncio.run(service.correct(PERSIAN_TEXT))

    assert result == "متن اصلاح‌شده"
    assert provider.calls == [(PERSIAN_PROOFREADING_SYSTEM_PROMPT, PERSIAN_TEXT)]


def test_service_propagates_provider_errors() -> None:
    provider = _RecordingProvider(error=ProviderUnavailableError("down"))
    service = LLMCorrectionService(provider)

    with pytest.raises(ProviderUnavailableError):
        asyncio.run(service.correct(PERSIAN_TEXT))


def test_dependency_builds_an_llm_backed_service(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "correction_provider", GROQ_PROVIDER)

    service = get_correction_service()

    assert isinstance(service, LLMCorrectionService)


# --- End-to-end through POST /api/v1/correct --------------------------------


@pytest.mark.parametrize("provider", DEFINED_PROVIDERS)
def test_endpoint_returns_the_provider_correction(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
) -> None:
    body, _ = _builders(provider)
    monkeypatch.setattr(settings, "correction_provider", provider)
    provider_transport.respond(lambda _: httpx.Response(200, json=body(CORRECTED_TEXT)))

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 200
    assert response.json() == {"corrected_text": CORRECTED_TEXT}


def test_endpoint_sends_the_correction_prompt_to_groq(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", GROQ_PROVIDER)
    monkeypatch.setattr(settings, "groq_model", "openai/gpt-oss-120b")
    provider_transport.respond(lambda _: httpx.Response(200, json=_groq_body("ok")))

    provider_client.post(CORRECT_URL, json={"text": "متن"})

    body = json.loads(provider_transport.requests[0].content)
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["messages"] == [
        {"role": "system", "content": PERSIAN_PROOFREADING_SYSTEM_PROMPT},
        {"role": "user", "content": "متن"},
    ]


def test_endpoint_sends_the_correction_prompt_to_gemini(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", GEMINI_PROVIDER)
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.5-custom")
    provider_transport.respond(lambda _: httpx.Response(200, json=_gemini_body("ok")))

    provider_client.post(CORRECT_URL, json={"text": "متن"})

    request = provider_transport.requests[0]
    body = json.loads(request.content)
    assert body["systemInstruction"] == {
        "parts": [{"text": PERSIAN_PROOFREADING_SYSTEM_PROMPT}]
    }
    assert body["contents"] == [{"parts": [{"text": "متن"}]}]
    # The configured model ID selects the generateContent resource.
    assert "/models/gemini-3.5-custom:generateContent" in str(request.url)


@pytest.mark.parametrize("provider", DEFINED_PROVIDERS)
@pytest.mark.parametrize(
    ("status_code", "expected_status", "expected_code"),
    [
        (400, 500, INTERNAL_ERROR),
        (401, 502, PROVIDER_AUTH_ERROR),
        (403, 502, PROVIDER_AUTH_ERROR),
        (429, 429, PROVIDER_RATE_LIMIT),
        (500, 503, PROVIDER_UNAVAILABLE),
        (503, 503, PROVIDER_UNAVAILABLE),
        (504, 504, PROVIDER_TIMEOUT),
    ],
)
def test_endpoint_maps_provider_failures_to_documented_errors(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
    status_code: int,
    expected_status: int,
    expected_code: str,
) -> None:
    _, error_body = _builders(provider)
    monkeypatch.setattr(settings, "correction_provider", provider)
    provider_transport.respond(lambda _: httpx.Response(status_code, json=error_body(status_code)))

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == expected_status
    body = response.json()
    assert body["error"] == expected_code
    assert "corrected_text" not in body


@pytest.mark.parametrize("provider", DEFINED_PROVIDERS)
def test_endpoint_timeout_is_a_gateway_timeout(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", provider)

    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    provider_transport.respond(handler)

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 504
    assert response.json()["error"] == PROVIDER_TIMEOUT


@pytest.mark.parametrize("provider", DEFINED_PROVIDERS)
def test_endpoint_connection_error_is_provider_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", provider)

    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider_transport.respond(handler)

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 503
    assert response.json()["error"] == PROVIDER_UNAVAILABLE


@pytest.mark.parametrize("provider", DEFINED_PROVIDERS)
def test_endpoint_empty_provider_output_is_not_a_success(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", provider)
    empty_body = {"choices": []} if provider == GROQ_PROVIDER else {"candidates": []}
    provider_transport.respond(lambda _: httpx.Response(200, json=empty_body))

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == INTERNAL_ERROR
    assert "corrected_text" not in body


@pytest.mark.parametrize("provider", DEFINED_PROVIDERS)
def test_endpoint_never_leaks_provider_detail_or_credentials(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", provider)
    api_key = _api_key_for(provider)
    provider_transport.respond(
        lambda _: httpx.Response(
            503,
            json=_error_body_echoing(provider, f"backend overloaded for key {api_key}"),
        )
    )

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 503
    assert response.json()["error"] == PROVIDER_UNAVAILABLE
    assert api_key not in response.text
    assert "backend overloaded" not in response.text
