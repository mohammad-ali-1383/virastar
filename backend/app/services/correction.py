"""Correction service boundary and the Gemini-backed implementation.

The HTTP layer validates input and delegates proofreading to a
``CorrectionService``; how the text is corrected stays behind this interface
(`architecture.md`, section 3). :class:`GeminiCorrectionService` owns the fixed
proofreading prompt and sends the user's text to the LLM adapter separately
(`correction-prompt.md` -> Implementation Rules).

Keeping this layer provider-agnostic lets V2 add a second adapter without
changing the API contract.
"""

from __future__ import annotations

from typing import Protocol

from app.config import settings
from app.services.gemini import GeminiProvider
from app.services.prompt import PERSIAN_PROOFREADING_SYSTEM_PROMPT


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


class GeminiCorrectionService:
    """Proofreading workflow backed by the Gemini LLM adapter.

    The service owns the correction prompt; the adapter owns provider-specific
    authentication, requests, and response parsing.
    """

    def __init__(self, provider: GeminiProvider) -> None:
        self._provider = provider

    async def correct(self, text: str) -> str:
        return await self._provider.generate(
            system_instruction=PERSIAN_PROOFREADING_SYSTEM_PROMPT,
            user_text=text,
        )


def get_correction_service() -> CorrectionService:
    """FastAPI dependency returning the Gemini-backed correction service.

    The provider is built from the current settings on every request so a
    configuration change (environment variable or ``.env``) takes effect
    without recreating the application.
    """
    return GeminiCorrectionService(GeminiProvider.from_settings(settings))
