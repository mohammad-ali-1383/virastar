"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the env files from this module's location instead of the current
# working directory, so the same configuration works whether the process is
# started from the repository root, from ``backend/``
# (``cd backend && uvicorn app.main:app``), or in a container (``WORKDIR /app``).
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent

# The shared, git-ignored secret file at the repository root is the documented
# location for both Docker Compose and local runs. ``backend/.env`` is still
# honored for backward compatibility and, being listed second, takes precedence.
_ENV_FILES = (_REPO_ROOT / ".env", _BACKEND_DIR / ".env")


class Settings(BaseSettings):
    """Runtime settings for the backend service.

    Values are read from environment variables and/or a local ``.env`` file.
    Secrets must never be hardcoded here.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"

    # Maximum accepted text length. Configurable per `api-contract.md`.
    max_text_length: int = 1000

    # Development origins allowed by CORS (`architecture.md`, section 4).
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # --- LLM provider (Google Gemini Developer API, `tech-stack.md`) ---
    # Secret: read from the environment only and never logged or returned.
    # ``SecretStr`` keeps the value out of reprs, tracebacks, and logs.
    gemini_api_key: SecretStr = SecretStr("")

    # Model ID verified against the official Gemini documentation. Stable,
    # free-tier Flash text model recommended for new projects; overridable so a
    # model change needs no code change (`api-contract.md` -> Compatibility).
    gemini_model: str = "gemini-3.8-flash"

    # Gemini Developer API base URL and per-request timeout (`architecture.md`,
    # section 3: configuration owns model settings, endpoints, and timeouts).
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com"
    gemini_timeout_seconds: float = 30.0


settings = Settings()


def get_max_text_length() -> int:
    """FastAPI dependency: the currently configured maximum text length.

    The value is read on every request so a configuration change (environment
    variable or `.env`) takes effect without recreating the application.
    """
    return settings.max_text_length
