"""Public correction endpoint (`POST /api/v1/correct`)."""

from fastapi import APIRouter, Depends

from app.config import get_max_text_length
from app.errors import InternalError, InvalidInputError, TextTooLongError
from app.schemas import CorrectRequest, CorrectResponse, ErrorResponse
from app.services.correction import CorrectionService, get_correction_service

router = APIRouter(prefix="/api/v1", tags=["correction"])

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "INVALID_INPUT or TEXT_TOO_LONG"},
    429: {"model": ErrorResponse, "description": "PROVIDER_RATE_LIMIT"},
    502: {"model": ErrorResponse, "description": "PROVIDER_AUTH_ERROR"},
    503: {"model": ErrorResponse, "description": "PROVIDER_UNAVAILABLE"},
    504: {"model": ErrorResponse, "description": "PROVIDER_TIMEOUT"},
    500: {"model": ErrorResponse, "description": "INTERNAL_ERROR"},
}


@router.post(
    "/correct",
    response_model=CorrectResponse,
    responses=ERROR_RESPONSES,
    summary="Correct Persian text",
)
async def correct_text(
    payload: CorrectRequest,
    service: CorrectionService = Depends(get_correction_service),
    max_text_length: int = Depends(get_max_text_length),
) -> CorrectResponse:
    """Validate the submitted text and return its corrected form."""
    # Validation is enforced here (never only in the frontend) and the length
    # is measured after trimming, as required by api-contract.md.
    text = payload.text.strip()

    if not text:
        raise InvalidInputError("text is empty after trimming")

    if len(text) > max_text_length:
        raise TextTooLongError(f"text length {len(text)} > limit {max_text_length}")

    corrected_text = await service.correct(text)

    # A provider that returns nothing usable is a failure, not a success.
    if not corrected_text or not corrected_text.strip():
        raise InternalError("correction service returned empty text")

    return CorrectResponse(corrected_text=corrected_text)
