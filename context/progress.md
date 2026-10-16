# Project Progress

## Current Version
V1 — MVP Website

## Overall Status
`IN_PROGRESS` — Phases 2 and 3 are implemented and verified in a pinned environment. The correction
endpoint is now backed by a real Google Gemini adapter (`MODEL-001`); the live Persian proofreading
quality check against the real API is the remaining Phase 3 item. Environment configuration (which `.env` feeds which workflow) is verified and corrected (`MODEL-002`).

## V1 — MVP
- [x] Project setup — structure, config, Docker, and docs created and partly verified (see Verified Milestones and Known Issues)
- [x] Backend API — `POST /api/v1/correct` with backend validation, the configurable length limit, and the documented success/error formats (`BACKEND-001`)
- [x] Single LLM provider integration — Google Gemini `gemini-3.8-flash` adapter behind the unchanged `CorrectionService` interface (`MODEL-001`); mocked tests pass, live quality check pending
- [ ] Website implementation
- [ ] Integration and acceptance tests
- [ ] Deployment

## V2 — Multiple LLM Providers
- [ ] Add fallback provider
- [ ] Test fallback and failure handling

## V3 — Telegram Bot
- [ ] Create Telegram bot
- [ ] Connect bot to existing backend
- [ ] Test complete message flow

## Verified Milestones
- 2026-10-15 — Configuration (MODEL-002): verified how `GEMINI_API_KEY` and `GEMINI_MODEL` reach the backend. Docker Compose was already correct (`env_file: .env` at the repository root; `docker compose config` resolves the key and model into the backend service environment). Local Uvicorn was misconfigured: `Settings` resolved `env_file=".env"` against the current working directory, so the documented root `.env` was ignored by `cd backend && uvicorn app.main:app` and only `backend/.env` was read. Fixed with absolute, root-first env-file resolution derived from the module location.
- 2026-10-15 — Configuration (MODEL-002): behaviour probes from `backend/` confirmed the fix — a root-only `.env` is now read; when both files exist `backend/.env` wins; real environment variables beat both (so Compose is unchanged); the same root `.env` is read when the process starts from the repository root; the resolved env-file paths are absolute. Probe values were the model ID only — no real key was created, read, or printed.
- 2026-10-15 — Configuration (MODEL-002): `cd backend && pytest -q` → **97 passed** (exit 0), up from 93. Four new tests in `tests/test_config.py` lock the fix (a CWD-relative `.env` path or one omitting the root file now fails) and confirm root-plus-backend precedence and CWD independence.
- 2026-10-15 — Configuration (MODEL-002): `git check-ignore` confirms `.env`, `backend/.env`, and `frontend/.env` are ignored while `.env.example` stays tracked (the `!.env.example` negation wins over `.env.*`). All probe `.env` files were deleted afterwards.
- 2026-10-15 — Phase 3 (MODEL-001): Gemini provider facts verified before implementation — model `gemini-3.8-flash` (stable, free-tier, named by Google for new projects), `POST /v1beta/models/{model}:generateContent` at `https://generativelanguage.googleapis.com`, `x-goog-api-key` header auth, `systemInstruction` + separate `contents` request shape, and the documented error codes. Cross-checked against `context/tech-stack.md` (same candidate model) and current independent sources; `ai.google.dev` itself returned HTTP 403 to this environment's page fetcher.
- 2026-10-15 — Phase 3 (MODEL-001): `cd backend && pytest -q` → **93 passed** (exit 0). New coverage: success path returns the provider's corrected text; the fixed prompt is sent as the Gemini `systemInstruction` with the user's text in a separate `contents` entry; the key is sent in the `x-goog-api-key` header and never appears in the URL; `401`/`403` → `PROVIDER_AUTH_ERROR`, `429` → `PROVIDER_RATE_LIMIT`, `504` and read timeouts → `PROVIDER_TIMEOUT`, `500`/`502`/`503`/`404`/connection errors → `PROVIDER_UNAVAILABLE`, `400` → `INTERNAL_ERROR`; empty/blank/malformed/candidate-less model output and missing `GEMINI_API_KEY` never produce a fake success; raw provider messages and the key never appear in responses or error details. All provider calls use `httpx.MockTransport` — no real key, no network.
- 2026-10-15 — Phase 3 (MODEL-001): live app wiring with no key (FastAPI test client against the unmodified `app.main:app`): `/health` → 200; valid text → `502 PROVIDER_AUTH_ERROR`; whitespace text and missing field → `400 INVALID_INPUT`; 1001 characters → `400 TEXT_TOO_LONG`; `python -m compileall app tests` succeeds. Settings repr shows `gemini_api_key=SecretStr('')`, so the secret is not logged.
- 2026-10-14 — Phase 2 (BACKEND-001): `cd backend && pytest -q` → **36 passed** (exit 0) with the pinned versions (`fastapi==0.143.1`, `pydantic==2.14.1`, `pydantic-settings==2.15.0`, `httpx==0.28.1`, `pytest==9.1.1`). Coverage: documented success shape; empty, whitespace-only, missing, null, wrong-type, non-JSON, and malformed-JSON requests → `400 INVALID_INPUT`; exactly 1000 characters accepted; 1001 characters → `400 TEXT_TOO_LONG` with the documented message; the limit overridable through `MAX_TEXT_LENGTH`; provider failures mapped to 503/504/429/502; empty or whitespace-only provider output → `500 INTERNAL_ERROR`; raw provider detail never present in a response; `/health` unchanged.
- 2026-10-14 — Phase 2 (BACKEND-001): live `uvicorn app.main:app` on the host confirmed the contract over HTTP — `/health` 200; valid text 200 with `corrected_text`; padded text 200 (trimmed); empty, missing, and null text 400 `INVALID_INPUT`; 1000 characters 200; 1001 characters 400 `TEXT_TOO_LONG`.
- 2026-10-14 — Phase 2 (BACKEND-001): `docker build` of the unmodified `backend/Dockerfile` (Python 3.12) succeeded and the running container reproduced all of the results above; container logs contain only the error code and metadata (e.g. the text length), never the submitted text.
- 2026-10-14 — Environment: the `files.pythonhosted.org` blockage recorded in Phase 1/FIX-001 no longer reproduces from the host, so `pip install -r backend/requirements-dev.txt` and the Docker image build complete at the exact pinned versions.
- 2026-10-14 — Phase 1 (SETUP-001): frontend dependencies installed at pinned versions and `npm run build` (TypeScript type check + Vite build) passes.
- 2026-10-14 — Phase 1 (SETUP-001): Vite dev server starts on port 5173 and serves the Persian RTL page (HTTP 200), then stops cleanly.
- 2026-10-14 — Phase 1 (SETUP-001): backend `app/` and `tests/` compile (`compileall`), and `app/config.py` default/override behaviour verified (max length default 1000, overridable; development CORS origins present).
- 2026-10-14 — Phase 1 (SETUP-001): `docker compose config` validates.
- 2026-10-14 — Phase 1 (SETUP-001): `.gitignore` rules verified with `git check-ignore` (`.env` ignored, `.env.example` tracked; `node_modules`, `dist`, `.venv`, `__pycache__` ignored).

## Known Issues
- 2026-10-15 — [resolved by `MODEL-002`] The documented root `.env` was ignored by local runs because `env_file=".env"` is CWD-relative; a local dev following `README.md` would have seen `502 PROVIDER_AUTH_ERROR` with no key loaded. Resolution is now absolute and root-first, so one root `.env` serves both Compose and local Uvicorn.
- 2026-10-15 — [`MODEL-001`] Real Persian proofreading quality against the live Gemini API has not been run: no API key was used, because that is a real (potentially billable) provider call and the automated suite must not make real calls. The integration is verified with mocked responses only; run the steps in `README.md` with a key to complete the Phase 3 quality check.
- 2026-10-15 — [`MODEL-001`] `ai.google.dev` (official Gemini docs) returns HTTP 403 to this environment's page fetcher, so provider facts were verified from current independent sources and `context/tech-stack.md` rather than the doc pages directly. The model ID and endpoint are configuration values (`GEMINI_MODEL`, `GEMINI_API_BASE_URL`) and can be changed without code changes if Google renames the model.
- 2026-10-14 — [resolved by `MODEL-001`] `POST /api/v1/correct` returned the submitted text unchanged; `PassthroughCorrectionService` was the Phase 2 placeholder and called no provider. It has been replaced by `GeminiCorrectionService` + the Gemini adapter.
- 2026-10-14 — [`BACKEND-001`] The `virastare-backend:latest` image on this machine was built before the Phase 2 code, so it does not contain the endpoint. Rebuild with `docker compose up --build` or `cd backend && docker build -t virastare-backend .`.
- 2026-10-14 — [`BACKEND-001`] The host has Python 3.10 only (`backend/.venv` was recreated because the previous environment was empty; the `Python313` directory has no interpreter). The pinned dependencies install and the full suite passes on 3.10, and the container run on Python 3.12 reproduces the same behaviour, but `README.md` documents Python 3.12+ as the supported runtime.
- 2026-10-14 — [Phase 1, resolved] "Backend tests were NOT executed" and "pip install cannot complete" were caused by the `files.pythonhosted.org` blockage documented in `current-task.md` (FIX-001/FIX-002). Both are resolved in this session; the backend suite now runs and passes.

## Update Rules
- Mark tasks complete only after verification.
- Record important test results and unresolved issues.
- Keep entries concise and factual.
- Keep the active task in `current-task.md`.
- Follow `task-plan.md` for implementation order.
