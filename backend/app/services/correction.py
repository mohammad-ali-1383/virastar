"""Correction service boundary and the configured-provider implementation.

The HTTP layer validates input and delegates proofreading to a
``CorrectionService``; how the text is corrected stays behind this interface
(`architecture.md`, section 3). :class:`LLMCorrectionService` owns the fixed
proofreading prompt and sends the user's text to the LLM adapter separately
(`correction-prompt.md` -> Implementation Rules).

Two adapters are supported in V1 — Groq and Google Gemini — and the active one
is chosen explicitly by ``CORRECTION_PROVIDER``. Selection never falls back: an
unrecognized value is a configuration error, so a misconfigured deployment
cannot silently talk to a provider the operator did not choose.
"""

from __future__ import annotations

from typing import Protocol

from app.config import settings
from app.errors import InternalError
from app.services.gemini import GeminiProvider
from app.services.groq import GroqProvider
from app.services.prompt import PERSIAN_PROOFREADING_SYSTEM_PROMPT

# Names accepted by ``CORRECTION_PROVIDER`` (`tech-stack.md`).
GROQ_PROVIDER = "groq"
GEMINI_PROVIDER = "gemini"


class LLMProvider(Protocol):
    """Interface implemented by every provider adapter."""

    async def generate(self, *, system_instruction: str, user_text: str) -> str:
        """Return the provider's correction of ``user_text``.

        Implementations must return non-empty corrected text and raise a
        :class:`~app.errors.CorrectionError` subclass when they cannot, rather
        than fabricating a correction.
        """
        ...


class CorrectionService(Protocol):
    """Interface implemented by every correction strategy."""

    async def correct(self, text: str) -> str:
        """Return the corrected form of ``text``.

        ``text`` is already validated, non-empty, and within the configured
        length limit. Implementations must return non-empty corrected text and
        raise a :class:`~app.errors.CorrectionError` subclass when they cannot,
        rather than fabricating a correction.
        """
        ...


class LLMCorrectionService:
    """Proofreading workflow backed by one LLM adapter.

    The service owns the correction prompt; the adapter owns provider-specific
    authentication, requests, and response parsing.
    """

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def correct(self, text: str) -> str:
        return await self._provider.generate(
            system_instruction=PERSIAN_PROOFREADING_SYSTEM_PROMPT,
            user_text=text,
        )


def build_provider(provider_name: str) -> LLMProvider:
    """Return the adapter for ``provider_name``.

    The name is matched case-insensitively and explicitly; an unknown value
    raises :class:`~app.errors.InternalError` instead of falling back to a
    default provider.
    """
    normalized = provider_name.strip().lower()

    if normalized == GROQ_PROVIDER:
        return GroqProvider.from_settings(settings)

    if normalized == GEMINI_PROVIDER:
        return GeminiProvider.from_settings(settings)

    raise InternalError(f"unsupported CORRECTION_PROVIDER: {normalized[:32]!r}")


def get_correction_service() -> CorrectionService:
    """FastAPI dependency returning the service for the configured provider.

    The provider is built from the current settings on every request so a
    configuration change (environment variable or ``.env``) takes effect
    without recreating the application.
    """
    return LLMCorrectionService(build_provider(settings.correction_provider))
