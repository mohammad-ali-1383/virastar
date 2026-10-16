"""FastAPI application entry point.

Phase 2 exposes the health endpoint and the public correction API
(``POST /api/v1/correct``). The correction service behind that endpoint is a
placeholder until the LLM adapter is integrated in Phase 3.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import register_exception_handlers
from app.routers.correction import router as correction_router

app = FastAPI(
    title="Persian Writing Assistant API",
    description="Backend API for the Persian proofreading service.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

register_exception_handlers(app)

app.include_router(correction_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and local checks."""
    return {"status": "ok"}
