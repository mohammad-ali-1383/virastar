"""Pydantic models for the public API (`api-contract.md`).

The models describe the wire format only; validation of the configured text
limit lives in the API layer because the limit is runtime configuration.
"""

from pydantic import BaseModel, Field


class CorrectRequest(BaseModel):
    """Request body of ``POST /api/v1/correct``."""

    text: str = Field(description="Persian text to proofread.")


class CorrectResponse(BaseModel):
    """Successful response body."""

    corrected_text: str = Field(description="Corrected Persian text.")


class ErrorResponse(BaseModel):
    """Error body shared by every documented error code."""

    error: str = Field(description="Machine-readable error code.")
    message: str = Field(description="Human-readable Persian message.")
