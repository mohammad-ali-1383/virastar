"""Public error contract for the API.

Every error response uses the structure documented in `api-contract.md`::

    {"error": "ERROR_CODE", "message": "..."}

:class:`CorrectionError` keeps the public ``message`` and the internal
``detail`` in separate attributes, so provider errors and other internal
information are never serialised into a response.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Public error codes (`api-contract.md` → Error Codes).
INVALID_INPUT = "INVALID_INPUT"
TEXT_TOO_LONG = "TEXT_TOO_LONG"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
PROVIDER_AUTH_ERROR = "PROVIDER_AUTH_ERROR"
INTERNAL_ERROR = "INTERNAL_ERROR"


class CorrectionError(Exception):
    """Base class for failures that map to a documented API error response.

    Subclasses declare the public ``code``, ``http_status``, and ``message``.
    ``detail`` is optional context for server-side logs only.

    Provider adapters (Phase 3) raise these errors instead of returning
    invented text; see `coding-rules.md` → LLM Integration.
    """

    code: str = INTERNAL_ERROR
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "خطای داخلی سرور رخ داد."

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.code)
        self.detail = detail


class InvalidInputError(CorrectionError):
    """Missing, empty, or malformed input."""

    code = INVALID_INPUT
    http_status = status.HTTP_400_BAD_REQUEST
    message = "متن ارسالی نامعتبر است."


class TextTooLongError(CorrectionError):
    """Text longer than the configured maximum length."""

    code = TEXT_TOO_LONG
    http_status = status.HTTP_400_BAD_REQUEST
    message = "متن واردشده بیش از حداکثر مجاز است."


class ProviderUnavailableError(CorrectionError):
    """The LLM provider could not be reached or returned a server error."""

    code = PROVIDER_UNAVAILABLE
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    message = "سرویس اصلاح متن در حال حاضر در دسترس نیست."


class ProviderTimeoutError(CorrectionError):
    """The LLM request exceeded the configured timeout."""

    code = PROVIDER_TIMEOUT
    http_status = status.HTTP_504_GATEWAY_TIMEOUT
    message = "زمان انتظار برای پاسخ سرویس اصلاح متن به پایان رسید."


class ProviderRateLimitError(CorrectionError):
    """The provider reported a rate or quota limit."""

    code = PROVIDER_RATE_LIMIT
    http_status = status.HTTP_429_TOO_MANY_REQUESTS
    message = "محدودیت استفاده از سرویس اصلاح متن فعال شده است. لطفاً بعداً تلاش کنید."


class ProviderAuthError(CorrectionError):
    """Provider authentication or authorisation failed."""

    code = PROVIDER_AUTH_ERROR
    http_status = status.HTTP_502_BAD_GATEWAY
    message = "ارتباط با سرویس اصلاح متن با خطا مواجه شد."


class InternalError(CorrectionError):
    """Unexpected internal failure, including invalid provider responses."""

    code = INTERNAL_ERROR
    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "خطای داخلی سرور رخ داد."


def error_response(code: str, message: str, http_status: int) -> JSONResponse:
    """Build the documented error body."""
    return JSONResponse(
        status_code=http_status,
        content={"error": code, "message": message},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Guarantee the documented error format for every failure.

    FastAPI's default validation response (``422`` with a ``detail`` list) and
    its bare ``500`` are both replaced by the contract structure.
    """

    @app.exception_handler(CorrectionError)
    async def handle_correction_error(_: Request, exc: CorrectionError) -> JSONResponse:
        if exc.detail:
            logger.warning("Correction error %s: %s", exc.code, exc.detail)
        return error_response(exc.code, exc.message, exc.http_status)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _: Request, __: RequestValidationError
    ) -> JSONResponse:
        # Malformed JSON, missing fields, and wrong types are all invalid input.
        return error_response(
            InvalidInputError.code, InvalidInputError.message, InvalidInputError.http_status
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        # Log the exception type only: user text and provider payloads stay out
        # of the logs, and no stack trace is returned to the client.
        logger.error("Unhandled error: %s", type(exc).__name__)
        return error_response(InternalError.code, InternalError.message, InternalError.http_status)
