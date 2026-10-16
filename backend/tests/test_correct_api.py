"""Tests for ``POST /api/v1/correct`` (`api-contract.md`, `testing.md`)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.errors import (
    INTERNAL_ERROR,
    INVALID_INPUT,
    PROVIDER_AUTH_ERROR,
    PROVIDER_RATE_LIMIT,
    PROVIDER_TIMEOUT,
    PROVIDER_UNAVAILABLE,
    TEXT_TOO_LONG,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from tests.conftest import StubCorrectionService

CORRECT_URL = "/api/v1/correct"

# Documented message for TEXT_TOO_LONG (`api-contract.md` → Error Response).
TEXT_TOO_LONG_MESSAGE = "متن واردشده بیش از حداکثر مجاز است."

PERSIAN_TEXT = "سلام، این یک متن آزمایشی است."


# --- Success path -----------------------------------------------------------


def test_valid_text_returns_documented_success_shape(
    client: TestClient, stub_service: StubCorrectionService
) -> None:
    stub_service.result = "سلام، این یک متن آزمایشی است."

    response = client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"corrected_text": "سلام، این یک متن آزمایشی است."}
    assert list(response.json()) == ["corrected_text"]


def test_valid_text_returns_non_empty_corrected_text(
    client: TestClient, stub_service: StubCorrectionService
) -> None:
    response = client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 200
    assert response.json()["corrected_text"].strip()


def test_text_is_trimmed_before_it_reaches_the_service(
    client: TestClient, stub_service: StubCorrectionService
) -> None:
    client.post(CORRECT_URL, json={"text": "  متن  با  فاصله  "})

    # Inner spacing and line breaks are preserved, only the edges are trimmed.
    assert stub_service.received == ["متن  با  فاصله"]


def test_correction_route_is_registered(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "post" in paths["/api/v1/correct"]


def test_health_endpoint_still_works(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Invalid input ----------------------------------------------------------

INVALID_BODIES = [
    pytest.param({}, id="missing-text"),
    pytest.param({"text": None}, id="null-text"),
    pytest.param({"text": ""}, id="empty-text"),
    pytest.param({"text": "   "}, id="spaces-only"),
    pytest.param({"text": "\n\t \r\n"}, id="whitespace-only"),
    pytest.param({"text": 123}, id="wrong-type-number"),
    pytest.param({"text": ["متن"]}, id="wrong-type-list"),
]


@pytest.mark.parametrize("body", INVALID_BODIES)
def test_invalid_payloads_are_rejected(
    client: TestClient, body: dict[str, object]
) -> None:
    response = client.post(CORRECT_URL, json=body)

    assert response.status_code == 400
    assert response.json()["error"] == INVALID_INPUT


def test_unknown_fields_are_ignored(client: TestClient) -> None:
    response = client.post(CORRECT_URL, json={"text": PERSIAN_TEXT, "extra": "ignored"})

    assert response.status_code == 200


def test_malformed_json_is_rejected(client: TestClient) -> None:
    response = client.post(
        CORRECT_URL,
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == INVALID_INPUT


def test_non_json_body_is_rejected(client: TestClient) -> None:
    response = client.post(CORRECT_URL, content="متن ساده بدون JSON")

    assert response.status_code == 400
    assert response.json()["error"] == INVALID_INPUT


def test_validation_error_does_not_reach_the_service(
    client: TestClient, stub_service: StubCorrectionService
) -> None:
    client.post(CORRECT_URL, json={"text": "   "})

    assert stub_service.received == []


# --- Length boundary --------------------------------------------------------


def test_text_of_exactly_max_length_is_accepted(
    client: TestClient, stub_service: StubCorrectionService
) -> None:
    text = "ا" * 1000

    response = client.post(CORRECT_URL, json={"text": text})

    assert response.status_code == 200
    assert response.json() == {"corrected_text": text}
    assert len(stub_service.received[0]) == 1000


def test_text_one_character_over_max_length_is_rejected(
    client: TestClient, stub_service: StubCorrectionService
) -> None:
    response = client.post(CORRECT_URL, json={"text": "ا" * 1001})

    assert response.status_code == 400
    assert response.json() == {
        "error": TEXT_TOO_LONG,
        "message": TEXT_TOO_LONG_MESSAGE,
    }
    assert stub_service.received == []


def test_length_limit_ignores_surrounding_whitespace(client: TestClient) -> None:
    text = "  " + "ا" * 1000 + "  \n"

    response = client.post(CORRECT_URL, json={"text": text})

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("length", "expected_status"),
    [(5, 200), (6, 400)],
)
def test_limit_is_configurable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    length: int,
    expected_status: int,
) -> None:
    monkeypatch.setattr(settings, "max_text_length", 5)

    response = client.post(CORRECT_URL, json={"text": "ا" * length})

    assert response.status_code == expected_status
    if expected_status == 400:
        assert response.json()["error"] == TEXT_TOO_LONG


# --- Provider failures ------------------------------------------------------


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (ProviderUnavailableError, 503, PROVIDER_UNAVAILABLE),
        (ProviderTimeoutError, 504, PROVIDER_TIMEOUT),
        (ProviderRateLimitError, 429, PROVIDER_RATE_LIMIT),
        (ProviderAuthError, 502, PROVIDER_AUTH_ERROR),
    ],
)
def test_provider_failures_map_to_documented_errors(
    client: TestClient,
    stub_service: StubCorrectionService,
    error: type[Exception],
    expected_status: int,
    expected_code: str,
) -> None:
    stub_service.error = error("raw provider detail: sk-live-000")

    response = client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == expected_status
    body = response.json()
    assert body["error"] == expected_code
    assert body["message"]
    # Never fabricate corrected text when the provider fails.
    assert "corrected_text" not in body
    # Raw provider details must not leak into the response.
    assert "sk-live-000" not in response.text


@pytest.mark.parametrize("empty_result", ["", "   ", "\n"])
def test_empty_provider_response_is_not_a_success(
    client: TestClient, stub_service: StubCorrectionService, empty_result: str
) -> None:
    stub_service.result = empty_result

    response = client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 500
    assert response.json()["error"] == INTERNAL_ERROR
    assert "corrected_text" not in response.json()


def test_unexpected_error_returns_documented_internal_error(
    tolerant_client: TestClient, stub_service: StubCorrectionService
) -> None:
    stub_service.error = RuntimeError("internal detail: sk-live-000")

    response = tolerant_client.post(CORRECT_URL, json={"text": PERSIAN_TEXT})

    assert response.status_code == 500
    assert response.json()["error"] == INTERNAL_ERROR
    assert "sk-live-000" not in response.text
    assert "Traceback" not in response.text


# --- Error format consistency ----------------------------------------------


def test_every_error_uses_the_documented_structure(
    client: TestClient, stub_service: StubCorrectionService
) -> None:
    stub_service.error = ProviderUnavailableError("provider down")

    responses = [
        client.post(CORRECT_URL, json={"text": ""}),
        client.post(CORRECT_URL, json={"text": "ا" * 1001}),
        client.post(CORRECT_URL, content="{not valid json", headers={"Content-Type": "application/json"}),
        client.post(CORRECT_URL, json={"text": PERSIAN_TEXT}),
    ]

    for response in responses:
        assert response.status_code >= 400
        body = json.loads(response.text)
        assert sorted(body) == ["error", "message"]
        assert isinstance(body["error"], str) and body["error"]
        assert isinstance(body["message"], str) and body["message"]
        assert "corrected_text" not in body
