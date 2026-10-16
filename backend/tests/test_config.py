"""Configuration tests: defaults and environment-driven overrides."""

from pathlib import Path

import pytest

import app.config as app_config
from app.config import Settings, settings

# Expected env-file locations, derived the same way the loader derives them.
_BACKEND_DIR = Path(app_config.__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent


def test_default_max_text_length() -> None:
    assert Settings(_env_file=None).max_text_length == 1000


def test_max_text_length_is_configurable() -> None:
    assert Settings(_env_file=None, max_text_length=42).max_text_length == 42


def test_default_cors_origins_are_development_origins() -> None:
    origins = Settings(_env_file=None).cors_origins

    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins


def test_module_settings_load() -> None:
    assert settings.max_text_length > 0


def test_max_text_length_is_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAX_TEXT_LENGTH", "55")

    assert Settings(_env_file=None).max_text_length == 55


@pytest.fixture
def root_env_file(tmp_path: Path) -> Path:
    """A root-style dotenv file (no real secrets, only the model ID)."""
    path = tmp_path / "root.env"
    path.write_text("GEMINI_MODEL=from-root-env\n", encoding="utf-8")
    return path


@pytest.fixture
def backend_env_file(tmp_path: Path) -> Path:
    path = tmp_path / "backend.env"
    path.write_text("GEMINI_MODEL=from-backend-env\n", encoding="utf-8")
    return path


def test_env_files_cover_the_repo_root_and_backend() -> None:
    # Guards MODEL-002: `.env` must not be resolved relative to the current
    # working directory, otherwise the documented root `.env` is ignored when
    # running `cd backend && uvicorn app.main:app`.
    env_files = tuple(Path(path) for path in Settings.model_config["env_file"])

    assert env_files == (_REPO_ROOT / ".env", _BACKEND_DIR / ".env")
    # Absolute paths are what make the lookup independent of the CWD.
    assert all(path.is_absolute() for path in env_files)


def test_root_env_file_works_from_any_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Changing the CWD must not change which env files the loader targets.
    monkeypatch.chdir(tmp_path)

    env_files = tuple(Path(path) for path in Settings.model_config["env_file"])

    assert env_files[0] == (_REPO_ROOT / ".env").resolve()


def test_later_env_file_wins(root_env_file: Path, backend_env_file: Path) -> None:
    # The loader lists the root file first and `backend/.env` second, so the
    # backend file overrides the root one. This locks that contract.
    loaded = Settings(_env_file=(root_env_file, backend_env_file))

    assert loaded.gemini_model == "from-backend-env"


def test_a_root_env_file_is_loaded(root_env_file: Path) -> None:
    # End-to-end check that a root-style `.env` value reaches the settings.
    loaded = Settings(_env_file=root_env_file)

    assert loaded.gemini_model == "from-root-env"


def test_default_gemini_model_is_the_verified_stable_flash_model() -> None:
    assert Settings(_env_file=None).gemini_model == "gemini-3.8-flash"


def test_gemini_model_is_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.6-flash")

    assert Settings(_env_file=None).gemini_model == "gemini-3.6-flash"


def test_gemini_api_key_defaults_to_empty_and_is_a_secret() -> None:
    default_settings = Settings(_env_file=None)

    assert default_settings.gemini_api_key.get_secret_value() == ""
    # The secret must not appear in reprs or logs.
    assert "hunter2" not in repr(Settings(_env_file=None, gemini_api_key="hunter2"))


def test_gemini_api_key_is_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "env-secret-key")

    assert Settings(_env_file=None).gemini_api_key.get_secret_value() == "env-secret-key"


def test_gemini_endpoint_and_timeout_defaults() -> None:
    default_settings = Settings(_env_file=None)

    assert default_settings.gemini_api_base_url == "https://generativelanguage.googleapis.com"
    assert default_settings.gemini_timeout_seconds > 0
