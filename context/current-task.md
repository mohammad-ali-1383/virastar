# Current Task

## Task ID
`CONFIG-AUDIT`

## Objective
Verify how every documented environment variable reaches the frontend and backend, confirm the
precedence between Compose `environment`, `env_file`, dotenv files, and application defaults, and
fix only the inconsistencies with the documented architecture. Development ports 5173/8000 and
the existing workflows were preserved; no service, feature, or deployment change was made.

## Verified findings
- **Compose previously shadowed the root `.env`.** `docker compose config` proved that
  `docker-compose.yml` set `APP_ENV`, `MAX_TEXT_LENGTH`, and `CORS_ORIGINS` in `environment:`,
  which takes precedence over `env_file: .env`. A root `.env` override for those three was
  silently ignored in Compose, contradicting the documented "one root `.env` configures the
  backend in both workflows" contract. The values matched the application defaults, so the
  previous default setup looked correct.
- **Resulting precedence (verified):** real environment variables > Compose `environment:` >
  root `.env` (`env_file`, `pydantic-settings`) > `backend/.env` (local runs only) > application
  defaults. Compose now overrides only `CORRECTION_LOG_PATH` (container path backed by the
  `./logs` mount), which is documented as container-specific.
- **Frontend:** Vite gives `process.env` precedence over `frontend/.env` (verified with
  `loadEnv`), so the Compose-injected `VITE_API_BASE_URL` wins in the stack. `frontend/.env`
  (from `frontend/.env.example`) applies only to a local `npm run dev`.
- **Secrets:** `.env`, `backend/.env`, and `frontend/.env` are git-ignored and untracked; both
  `.env.example` files are tracked, contain empty key values only, and no provider-key-like
  pattern appears in any tracked file.
- **Documented-but-inert settings:** `APP_ENV` is read into `Settings` but consumed nowhere, and
  the frontend character counter is a fixed 1000 independent of `MAX_TEXT_LENGTH`. Both are now
  described accurately in `README.md`; no behavior changed.

## Change summary
- `docker-compose.yml` — removed the redundant `APP_ENV`, `MAX_TEXT_LENGTH`, and `CORS_ORIGINS`
  entries (their application defaults are identical), so the root `.env` governs them; kept and
  documented the container-only `CORRECTION_LOG_PATH` and the frontend `VITE_API_BASE_URL`.
- `.env.example` — clarified that `CORRECTION_LOG_PATH` applies to local runs and is deliberately
  overridden by Compose. Still placeholders only.
- `README.md` — added the frontend env-file row, documented the precedence rules, listed
  `frontend/.env.example`, described `APP_ENV` as informational, and noted the fixed frontend
  1000-character counter.

## Verification
- `docker compose config -q` → exit 0.
- Isolated temp Compose project (probe values, no secrets): `APP_ENV=staging`,
  `MAX_TEXT_LENGTH=2500`, probe `CORS_ORIGINS`, and probe `GROQ_MODEL` all reached the backend
  service from the root `.env`; `CORRECTION_LOG_PATH` remained `/app/logs/corrections.jsonl`.
  With the `.env` removed, no overrides were present and the first three fall back to the
  application defaults.
- Ports preserved: backend `8000:8000`, frontend `5173:5173`.
- `cd backend && .venv/Scripts/python.exe -m pytest -q` → **274 passed**, exit 0 (one pre-existing
  Starlette/httpx deprecation warning).
- `cd frontend && npm run test` → **11 passed**, exit 0.
- `cd frontend && npm run build` → exit 0 (`tsc --noEmit` + `vite build`); `npm run typecheck` →
  exit 0.
- Frontend env plumbing: a build with `VITE_API_BASE_URL=http://probe.invalid:9999` contained the
  probe value in the bundle, proving the injected variable reaches the frontend.
- Git checks: `.env`, `backend/.env`, `frontend/.env` ignored and untracked; `.env.example` and
  `frontend/.env.example` not ignored and tracked; no key patterns in tracked files.

## Not verified
- The running containers were not started for this audit; the Compose wiring was verified with
  `docker compose config` and an isolated Compose project, not a live stack.
- No live provider call was made and no secret value was read, printed, or changed.

## Status
`COMPLETED`

---

## Previous Task — `ERROR-CONTRACT`
Aligned every client-facing error with one `{error, message}` envelope: `404 NOT_FOUND`,
`405 METHOD_NOT_ALLOWED` with the framework `Allow` header, other framework statuses as
`HTTP_ERROR`, every provider failure normalized to the generic `503 PROVIDER_UNAVAILABLE`, and
validation kept at `400`. The OpenAPI document no longer advertises the unused `422` response.
274 backend tests and 11 frontend tests passed; no frontend code change was required.

## Earlier Tasks
`TEST-HERMETIC`, `LOG-001`, `FALLBACK-001`, `PROMPT-001`, `MODEL-004`, `FRONTEND-001`,
`MODEL-003`, `MODEL-002`, `MODEL-001`, `BACKEND-001`, `FIX-002`/`FIX-001`, and `SETUP-001` are
recorded in `progress.md`.
