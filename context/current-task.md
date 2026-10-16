# Current Task

## Task ID
`MODEL-002`

## Objective
Verify exactly how `GEMINI_API_KEY` and `GEMINI_MODEL` reach the backend in both supported
workflows — Docker Compose and local Uvicorn — by inspecting the settings loader, `.env.example`,
`.gitignore`, and `docker-compose.yml`. Fix any misconfiguration with the smallest safe change,
keep secrets out of source control, frontend code, logs, and documentation, preserve existing tests,
and add a focused test if needed. No real API key is read, printed, or created, and no real provider
calls are made.

## Finding — a real local-run misconfiguration (confirmed, then fixed)
`Settings` used `env_file=".env"`, a path resolved against the **current working directory**.

| Probe (run from `backend/`) | Result before the fix |
|---|---|
| only root `.env` present | **ignored** — `GEMINI_MODEL` stayed at its default |
| only `backend/.env` present | read |
| both present | `backend/.env` won |

Docker Compose was already correct: `docker-compose.yml` declares `env_file: .env` relative to the
compose file, so the root `.env` reached the container. But the documented setup (`cp .env.example
.env` at the root, then Option B `cd backend && uvicorn app.main:app`) placed the secret where the
**local workflow never looked**, so a user following the README would get `502 PROVIDER_AUTH_ERROR`
with no clue why. `.env.example` and `.gitignore` also imply a single root `.env`.

## Fix (smallest safe change)
`backend/app/config.py` now resolves the env files from the module location instead of the CWD:

- `_BACKEND_DIR = Path(__file__).resolve().parents[1]`, `_REPO_ROOT = _BACKEND_DIR.parent`
- `env_file=(_REPO_ROOT / ".env", _BACKEND_DIR / ".env")`

Both paths are absolute, so the lookup is independent of where the process starts. The root file is
listed first and `backend/.env` second, so a local override still wins. Real environment variables
keep the highest priority, so the Compose path (which injects `.env` into the container environment)
is unchanged — no Compose, Dockerfile, or dependency change was needed.

## Verification (details in `progress.md`)
- Behavior probes from `backend/`: root-only `.env` now read; both present → `backend/.env` wins;
  process env beats both; the same root `.env` is read when the process starts from the repository
  root; resolved env-file paths are absolute.
- `docker compose config` resolves `GEMINI_MODEL` and `GEMINI_TIMEOUT_SECONDS` from the root `.env`
  into the backend service environment (probe values only, no key).
- `git check-ignore`: `.env`, `backend/.env`, and `frontend/.env` are ignored; `.env.example` is
  tracked (the `!.env.example` negation still wins over `.env.*`).
- `cd backend && pytest -q` → **97 passed** (exit 0), up from 93; the 4 new tests in
  `tests/test_config.py` lock the fix (a `.env` path that is relative to the CWD, or that omits the
  root file, now fails).
- All probe `.env` files were deleted afterwards; none were left behind.

## Changed files
- `backend/app/config.py` — CWD-independent, root-first env-file resolution.
- `backend/tests/test_config.py` — focused env-file location, CWD-independence, and precedence tests.
- `.env.example` — documents the single root `.env` and the `backend/.env` override.
- `README.md` — an "Environment file locations" table, Compose recreate-vs-restart guidance, and
  key-free commands to confirm the loaded configuration.
- No change to `docker-compose.yml`, `.gitignore`, `backend/Dockerfile`, or any dependency pin.

## Constraints respected
- No real API key requested, read, printed, or created; probe values were the model ID only.
- No real Gemini request was made.
- No secret was written to source control, frontend code, logs, or documentation.

## Status
`COMPLETED` — both workflows verified to receive `GEMINI_API_KEY` and `GEMINI_MODEL`; the local-run
misconfiguration is fixed and covered by tests.

---

## Previous Task — `MODEL-001`
Implemented Phase 3: replaced `PassthroughCorrectionService` with a real Google Gemini adapter while
preserving the `CorrectionService` interface and the `POST /api/v1/correct` contract. Provider facts
verified before implementation: model `gemini-3.8-flash` (stable, free-tier, named by Google for new
projects), `POST /v1beta/models/{model}:generateContent` at `https://generativelanguage.googleapis.com`,
`x-goog-api-key` header auth, `systemInstruction` plus a separate `contents` entry, and the documented
error codes. New modules `backend/app/services/prompt.py` and `backend/app/services/gemini.py`;
configuration `GEMINI_API_KEY` (`SecretStr`), `GEMINI_MODEL`, `GEMINI_API_BASE_URL`,
`GEMINI_TIMEOUT_SECONDS`. Provider failures map to the documented codes and never fabricate a
correction. Full detail, including the provider verification table and test coverage, is in
`progress.md` and `README.md`.

## Earlier Tasks
`BACKEND-001` (Phase 2 API), `FIX-002`/`FIX-001` (PyPI CDN diagnosis), and `SETUP-001` (Phase 1) are
recorded in `progress.md`.
