# Current Task

## Task ID
`LOG-001`

## Objective
Add an optional, consent-based correction log. When the user presses «اصلاح متن» the website must
show a Persian consent dialog **before** any request is sent, offering exactly two choices —
«موافقم، ذخیره شود» (correct and allow storing the original and corrected text for quality
evaluation) and «فقط متنم را اصلاح کن» (correct without storing either text). Both choices run the
correction; dismissing the dialog (Escape, backdrop, close button) sends no request at all.

The choice travels explicitly in the request (`store_for_evaluation`), the **backend** enforces it
(frontend-only enforcement is insufficient), and only a real JSON boolean counts. With consent, one
structured JSON Lines record is appended to `logs/corrections.jsonl` containing the timestamp with
timezone, the submitted text, the **provider and model that actually succeeded** (which is Gemini
when the Groq-first attempt failed), and the final corrected text. Without consent, neither text is
written to evaluation logs, and no exception path or application log may expose user text, API keys,
authorization headers, or provider response bodies. The log directory/file is created on demand and
stays out of Git. A failed write must not leak text, must not falsely report success, and must not
break the correction. The correction prompt, validation rules, successful response contract, and the
Groq-first/Gemini-fallback behavior must be preserved, with no duplicate provider calls.

Decisions made with the user before implementation: the consent field is **optional and defaults to
"do not store"**; a failed log write **returns the correction with `200` plus a sanitized warning**;
the frontend dialog is tested with **Vitest + Testing Library**.

## Change summary
- `backend/app/services/correction_log.py` (new) — `CorrectionLogStore` (append-only JSON Lines,
  directory/file created on demand, blocking write offloaded with `asyncio.to_thread`) and
  `record_line()` producing `timestamp` (ISO 8601 UTC), `original_text`, `provider`, `model`,
  `corrected_text` with `ensure_ascii=False`. An `OSError` is reported as a sanitized warning
  (exception class + configured path only) and returned as `False`; it is never raised, never
  retried, and never includes the text.
- `backend/app/services/correction.py` — `CorrectionResult(text, provider, model)` is now returned by
  `CorrectionService.correct`; `ProviderSlot` carries the adapter's model, so the record names the
  adapter that really produced the text (Gemini after a Groq failure).
- `backend/app/services/groq.py`, `gemini.py` — additive `model` property exposing the model ID each
  adapter sends; request construction, error mapping, and the prompt are untouched.
- `backend/app/schemas.py` — `CorrectRequest.store_for_evaluation: bool = False` with
  `strict=True`, so a string or number is `400 INVALID_INPUT` instead of an accidental opt-in.
- `backend/app/routers/correction.py` — owns consent enforcement: after a successful correction and
  only when the flag is true, it appends the record via the new `get_correction_log_store`
  dependency (path read per request from settings). The response body is unchanged.
- `backend/app/config.py` — `correction_log_path`, anchored to the repository root like the env
  files (`<repo root>/logs/corrections.jsonl`), overridable via `CORRECTION_LOG_PATH`.
- `.gitignore` — `logs/` ignored. `.env.example` — documented, commented-out `CORRECTION_LOG_PATH`.
  `docker-compose.yml` — `CORRECTION_LOG_PATH=/app/logs/corrections.jsonl` plus a `./logs:/app/logs`
  mount, so consented records survive a container recreate instead of living in the image layer.
- `backend/tests/test_correction_logging.py` (new, 29 tests) — consent both ways, record fields and
  timezone, one line per request, fallback logging of the successful provider/model through the real
  adapters, nothing written for a declined/absent flag, invalid input with consent storing nothing, a
  non-boolean flag rejected, safe failures for both an unwritable file and an uncreatable directory
  (200 + sanitized warning, no text/keys/traceback in the logs), recovery on the next request, and
  store-level unit tests. All with temporary log paths and mocked providers.
- `backend/tests/conftest.py` — the stub service now returns `CorrectionResult` and carries
  `provider`/`model`; a new **autouse** `correction_log_path` fixture points the log at `tmp_path`,
  so no test can append to the deployment's real log file.
- `backend/tests/test_correct_api.py`, `test_correction_service.py`, `test_config.py` — consent flag
  contract (default false, OpenAPI, non-boolean rejected), the result's provider/model, and the log
  path default/override.
- `frontend/src/ConsentDialog.tsx` (new) — modal Persian consent dialog with the two documented
  labels, Escape/backdrop/close dismissal, focus moved into the dialog.
- `frontend/src/App.tsx` — submit only opens the dialog; the request is sent after a choice, with the
  matching `store_for_evaluation` value; dismissal sends nothing.
- `frontend/src/api.ts` — `requestCorrection(text, { storeForEvaluation, signal })` always sends the
  flag explicitly; the response contract is unchanged.
- `frontend/src/App.test.tsx` (new, 11 tests) + `vitest` config in `vite.config.ts`, a `test` script,
  and pinned dev dependencies (`vitest`, `jsdom`, Testing Library).
- Docs — new `context/correction-logging.md`; updated `api-contract.md`, `ui.md`, `architecture.md`,
  `tech-stack.md`, `testing.md`, `project.md`, `task-plan.md`, and `README.md`.

## Verification (details in `progress.md`)
- `cd backend && pytest -q` → **270 passed** (exit 0), all provider traffic mocked, all log paths
  temporary; the suite leaves no `logs/` directory behind (an autouse fixture redirects the log to a
  temporary file so no test can touch a real `logs/corrections.jsonl`).
- `cd frontend && npm run test` → **11 passed** (exit 0).
- `cd frontend && npm run build` → **exit 0** (`tsc --noEmit` + `vite build`).
- Mutation checks: logging without checking consent fails 4 backend tests; letting write errors
  escape the store fails 4; recording the primary provider instead of the successful one fails 1;
  skipping the consent step in the UI fails 9 frontend tests; always sending
  `store_for_evaluation: true` fails 2. All sources were verified byte-identical (md5) after
  restore.

## Notes / constraints
- Mocked providers only: no live API call, no extra provider request (the fallback still makes at
  most one attempt per provider), and no `.env` secret was read, printed, or modified.
- The evaluation record deliberately contains user text; that is the consented exception. Every
  other log path stays text-free.
- Concurrency: records are single append-mode writes; two simultaneous requests could interleave
  writes on a filesystem without atomic append semantics (no lock is taken, to avoid serializing
  corrections).

## Status
`COMPLETED` — see `progress.md` for the recorded results.

---

## Previous Task — `FALLBACK-001`
Added the automatic Groq → Gemini fallback (Groq always first, one retry with Gemini on any
provider-related failure, single generic `503 PROVIDER_UNAVAILABLE` when both fail, sanitized
logging), removed `CORRECTION_PROVIDER` at the user's request, and covered it with 36 mocked
end-to-end tests plus mutation checks. `LOG-001` builds on that: the fallback now reports which
provider and model succeeded so the evaluation log can record them.

## Earlier Tasks
`PROMPT-001` (prompt rewrite), `MODEL-004` (selectable adapters, superseded by `FALLBACK-001`),
`FRONTEND-001` (Persian RTL MVP interface), `MODEL-003`, `MODEL-002`, `MODEL-001`, `BACKEND-001`,
`FIX-002`/`FIX-001`, and `SETUP-001` are recorded in `progress.md`.
