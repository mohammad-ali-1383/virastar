"""Tests for explicit provider selection (`CORRECTION_PROVIDER`).

Selection is driven by configuration and must never fall back to a different
provider. All provider traffic is mocked, so these tests need no key and make no
network request.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import settings
from app.errors import INTERNAL_ERROR, PROVIDER_AUTH_ERROR, InternalError
from app.services.correction import (
    GEMINI_PROVIDER,
    GROQ_PROVIDER,
    LLMCorrectionService,
    build_provider,
    get_correction_service,
)
from app.services.gemini import GEMINI_API_BASE_URL, GEMINI_API_VERSION, GeminiProvider
from app.services.groq import GROQ_CHAT_COMPLETIONS_URL, GroqProvider
from tests.conftest import GEMINI_TEST_KEY, GROQ_TEST_KEY, ProviderTransport

CORRECT_URL = "/api/v1/correct"
PERSIAN_TEXT = "سلام این یک متن ازمایشی است"

groq_url = GROQ_CHAT_COMPLETIONS_URL
gemini_url = f"{GEMINI_API_BASE_URL}/{GEMINI_API_VERSION}"


def _groq_body(text: str) -> dict[str, object]:
    return {
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
    }


def _gemini_body(text: str) -> dict[str, object]:
    return {"candidates": [{"content": {"role": "model", "parts": [{"text": text}]}}]}


def _request_headers(request: httpx.Request) -> str:
    """All request headers as one lower-cased string (httpx folds the names)."""
    return " ".join(f"{name}:{value}".lower() for name, value in request.headers.items())


# --- build_provider ---------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected_type"),
    [
        (GROQ_PROVIDER, GroqProvider),
        (GEMINI_PROVIDER, GeminiProvider),
        (" Groq ", GroqProvider),
        ("GEMINI", GeminiProvider),
    ],
)
def test_build_provider_returns_the_requested_adapter(
    name: str, expected_type: type[object]
) -> None:
    assert isinstance(build_provider(name), expected_type)


@pytest.mark.parametrize(
    "name",
    ["", "  ", "avalai", "openai", "grok", "gemini2", "groq,gemini"],
)
def test_unknown_provider_is_a_configuration_error_and_never_falls_back(
    name: str,
) -> None:
    # The documented internal error, not another provider's adapter.
    with pytest.raises(InternalError):
        build_provider(name)


def test_correction_service_wraps_the_selected_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", GEMINI_PROVIDER)

    service = get_correction_service()

    assert isinstance(service, LLMCorrectionService)


# --- End-to-end: configuration chooses the provider -------------------------


@pytest.mark.parametrize(
    ("provider", "expected_url", "body"),
    [
        (GROQ_PROVIDER, groq_url, _groq_body),
        (GEMINI_PROVIDER, gemini_url, _gemini_body),
    ],
)
def test_configured_provider_handles_the_request(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
    expected_url: str,
    body: Callable[[str], dict[str, object]],
) -> None:
    monkeypatch.setattr(settings, "correction_provider", provider)
    provider_transport.respond(lambda _: httpx.Response(200, json=body("متن اصلاح‌شده")))

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 200
    assert response.json() == {"corrected_text": "متن اصلاح‌شده"}
    # Exactly one request, to the endpoint of the configured provider only.
    assert len(provider_transport.requests) == 1
    assert expected_url in str(provider_transport.requests[0].url)


@pytest.mark.parametrize(
    ("provider", "expected_url", "body"),
    [
        (GROQ_PROVIDER, groq_url, _groq_body),
        (GEMINI_PROVIDER, gemini_url, _gemini_body),
    ],
)
def test_only_the_selected_providers_key_is_sent(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
    provider: str,
    expected_url: str,
    body: Callable[[str], dict[str, object]],
) -> None:
    monkeypatch.setattr(settings, "correction_provider", provider)
    provider_transport.respond(lambda _: httpx.Response(200, json=body("ok")))

    provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    request = provider_transport.requests[0]
    headers = _request_headers(request)
    other_key = GEMINI_TEST_KEY if provider == GROQ_PROVIDER else GROQ_TEST_KEY

    if provider == GROQ_PROVIDER:
        assert f"authorization:bearer {GROQ_TEST_KEY}" in headers
    else:
        assert f"x-goog-api-key:{GEMINI_TEST_KEY}" in headers

    # The other provider's credential must never be sent anywhere.
    assert other_key not in headers
    assert other_key not in str(request.url)
    assert other_key not in request.content.decode("utf-8")


def test_provider_selection_is_read_per_request(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", GROQ_PROVIDER)
    provider_transport.respond(lambda _: httpx.Response(200, json=_groq_body("ok")))
    provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    # Switching the configuration switches the provider without a restart.
    monkeypatch.setattr(settings, "correction_provider", GEMINI_PROVIDER)
    provider_transport.respond(lambda _: httpx.Response(200, json=_gemini_body("ok")))
    provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    urls = [str(request.url) for request in provider_transport.requests]
    assert groq_url in urls[0]
    assert gemini_url in urls[1]


# --- Missing keys and unknown provider values through the API ---------------


@pytest.mark.parametrize("provider", [GROQ_PROVIDER, GEMINI_PROVIDER])
def test_missing_provider_key_is_an_auth_error_without_a_provider_call(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider: str,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", provider)
    monkeypatch.setattr(settings, f"{provider}_api_key", SecretStr(""))

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 502
    assert response.json()["error"] == PROVIDER_AUTH_ERROR
    assert "corrected_text" not in response.json()
    # No request is attempted with an unconfigured credential.
    assert provider_transport.requests == []


def test_unknown_configured_provider_fails_the_request(
    monkeypatch: pytest.MonkeyPatch,
    provider_transport: ProviderTransport,
    provider_client: TestClient,
    provider_keys: None,
) -> None:
    monkeypatch.setattr(settings, "correction_provider", "avalai")

    response = provider_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == INTERNAL_ERROR
    assert "corrected_text" not in body
    # The misconfiguration is reported generically and no provider is called.
    assert "avalai" not in response.text
    assert provider_transport.requests == []
