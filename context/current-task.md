# Current Task

## Task ID
`MODEL-004`

## Objective
Make the LLM provider selectable for the existing Persian correction backend: **Groq** and
**Google Gemini** adapters behind the unchanged `CorrectionService` interface, chosen explicitly by
`CORRECTION_PROVIDER` (default `groq`). Requirements: server-side requests only (no key in the
frontend or logs), the fixed Persian proofreading prompt unchanged, the `POST /api/v1/correct`
contract, the 1000-character limit, safe error handling, and configurable timeouts preserved, no
silent provider switching, and mocked tests only (no live API calls).

## Change summary
- `backend/app/config.py` — provider selection and per-provider settings replace the AvalAI ones:
  `CORRECTION_PROVIDER` (`groq` default), `GROQ_API_KEY` (secret), `GROQ_MODEL`
  (`openai/gpt-oss-20b`), `GROQ_TIMEOUT_SECONDS`, `GEMINI_API_KEY` (secret), `GEMINI_MODEL`
  (`gemini-3.5-flash-lite`), `GEMINI_TIMEOUT_SECONDS`. Keys stay `SecretStr`, so they cannot appear
  in reprs, logs, or responses.
- `backend/app/services/groq.py` (new) — OpenAI-compatible adapter:
  `POST https://api.groq.com/openai/v1/chat/completions`, `Authorization: Bearer` header, prompt as
  the `system` message, the user's text as the `user` message, reply read from
  `choices[0].message.content`.
- `backend/app/services/gemini.py` (new) — Gemini Developer API adapter:
  `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`,
  `x-goog-api-key` header, prompt as `systemInstruction`, the user's text as a separate `contents`
  entry, reply read from `candidates[0].content.parts[].text`.
- `backend/app/services/correction.py` — provider-agnostic `LLMCorrectionService` plus an
  `LLMProvider` protocol, `build_provider()` and `get_correction_service()`. Selection is explicit:
  an unrecognized `CORRECTION_PROVIDER` raises `InternalError` (500) instead of falling back, and
  the configuration is read per request.
- `backend/app/services/avalai.py` and `backend/tests/test_avalai_provider.py` — removed (AvalAI is
  superseded; Groq and Gemini are the selectable providers).
- Tests — `tests/conftest.py` adds a mock provider transport (patches `httpx.AsyncClient` so the
  real adapter path runs with no key and no network) and placeholder key fixtures;
  `tests/test_groq_provider.py` and `tests/test_gemini_provider.py` cover both adapters;
  `tests/test_provider_selection.py` covers selection, key isolation, missing keys, and an unknown
  provider value; `tests/test_correction_service.py` covers the prompt split and the documented
  error mapping end-to-end for both providers; `tests/test_config.py` covers the new settings.
- `.env.example` — `CORRECTION_PROVIDER`, `GROQ_*`, and `GEMINI_*` with empty key placeholders.
- `README.md`, `context/tech-stack.md`, `context/task-plan.md`, `context/architecture.md`,
  `context/progress.md` — updated for the two selectable providers.

## Verification (details in `progress.md`)
- `cd backend && pytest -q` → **178 passed** (exit 0). All provider traffic is mocked; no key and no
  network request.
- `cd frontend && npm run build` → **exit 0** (`tsc --noEmit` + `vite build`); the frontend is
  provider-agnostic and unchanged.

## Notes / constraints
- No live provider request was made: the automated suite is fully mocked and no real key was read,
  printed, or stored. Confirming a real connection requires the operator steps in `README.md`.
- `CORRECTION_PROVIDER=groq` was appended to the root `.env` (byte-level append; no secret value
  read, printed, or modified). The root `.env` already holds a `GEMINI_API_KEY` from the earlier
  Gemini work, so switching to `CORRECTION_PROVIDER=gemini` makes real, live provider calls. The
  `GROQ_API_KEY` is not set, which is why the default configuration answers `502
  PROVIDER_AUTH_ERROR`. Leftover `AVALAI_*` entries are now unused and ignored.
- The frontend never learns which provider is active (`api-contract.md` → Compatibility).

## Status
`COMPLETED` — see `progress.md` for the recorded results.

---

## Previous Task — `FRONTEND-001`
Implemented the Persian RTL MVP interface (`frontend/src/api.ts`, `App.tsx`, `index.css`): a
1000-character counter, loading/result/copy/error states, and a client for `POST /api/v1/correct`
with the documented error codes mapped to safe Persian messages. Verified with `npm run build` and a
browser→backend CORS/routing probe that made no provider call.

## Earlier Tasks
`MODEL-003` (AvalAI integration, now superseded by `MODEL-004`), `MODEL-002`, `MODEL-001`,
`BACKEND-001`, `FIX-002`/`FIX-001`, and `SETUP-001` are recorded in `progress.md`.
