# Current Task

## Task ID
`PROMPT-001`

## Objective
Rewrite the fixed Persian proofreading system prompt (`PERSIAN_PROOFREADING_SYSTEM_PROMPT`) so the
instructions are explicit and in English while the corrected text stays Persian, and lock the new
behaviour with deterministic regression tests. The prompt must cover: context-aware typo correction
(«سلا» → «سلام») without guessing genuinely ambiguous words, register preservation (never formalize
«می‌خوام» into «می‌خواهم»), systematic proofreading (spelling, grammar, word boundaries, Persian
half-spaces, spacing, punctuation, typography), punctuation recovery including questions written
without punctuation, strict meaning preservation with the least invasive correction, and an output
format of corrected Persian text only (preserved line breaks, no commentary or quotation marks,
unchanged text when there is nothing to fix). `context/correction-prompt.md` must stay in sync with
the constant, and provider selection, the fallback policy, and live API usage must not change.

## Change summary
- `backend/app/services/prompt.py` — the rewritten system prompt (English instruction text with
  Persian examples only), docstring updated to state that it is the single source of truth, that it
  is mirrored in `context/correction-prompt.md`, and that
  `backend/tests/test_correction_prompt.py` keeps the two in sync. No provider, service, endpoint,
  schema, or configuration change.
- `context/correction-prompt.md` — the System Prompt section is synchronized verbatim with the
  constant; `Purpose` now mentions register, and `Implementation Rules` record the single-source
  rule and where the regression cases live.
- `backend/tests/test_correction_prompt.py` (new) — regression tests: the exact prompt text versus
  the specification document, English-only instructions (Persian restricted to the documented
  examples and half-space words), the six numbered rule groups, required instruction phrases, the
  named golden sample, and a documented Persian case set (`CorrectionCase`) covering missing
  question marks, half-spaces/word boundaries, spacing before punctuation, collapsed words,
  contextual typos, unchanged text, formal and colloquial register, and ambiguous word separation
  or typos that must not be guessed. Persian words needing a half-space are built from one `ZWNJ`
  constant so the tests do not depend on how a paste stores U+200C.
- `backend/tests/test_groq_provider.py` — the existing prompt guardrail now asserts the new prompt's
  role line and closing output rule; the full text and rule coverage are pinned by the new module.

## Verification (details in `progress.md`)
- `cd backend && pytest -q` → **240 passed** (exit 0), up from 178; all provider traffic mocked, no
  key read, no network request.
- Drift check: mutating the prompt text in memory makes
  `test_prompt_matches_the_specification_document` fail, so the document/constant sync has teeth.
- `cd frontend && npm run build` → **exit 0** (`tsc --noEmit` + `vite build`); the frontend is
  untouched.

## Notes / constraints
- These tests verify the *instruction* sent to the provider, not the model's output. Whether a live
  model reproduces the documented cases can only be shown by a real (potentially billable) API call,
  which this task did not make. The prompt is an instruction, not a guarantee of perfect
  proofreading.
- No provider selection, fallback behaviour, or configuration was touched (`correction.py`,
  `config.py`, `groq.py`, and `gemini.py` are unchanged).
- No secret was read, printed, or modified; no file under `context/` outside the prompt spec, task,
  and progress records was changed.

## Status
`COMPLETED` — see `progress.md` for the recorded results.

---

## Previous Task — `MODEL-004`
Made the LLM provider selectable: **Groq** and **Google Gemini** adapters behind the unchanged
`CorrectionService` interface, chosen explicitly by `CORRECTION_PROVIDER` (default `groq`), with
server-side-only keys, per-provider timeouts, and no silent fallback (an unknown value returns
`500 INTERNAL_ERROR`). Added `backend/app/services/groq.py` and `backend/app/services/gemini.py`,
extended `config.py` and `correction.py`, removed the AvalAI adapter and its tests, updated
`.env.example`, `README.md`, and the `context/` docs, and verified with 178 mocked tests plus a
browser-to-backend probe that made no provider call. Full record in `progress.md`.

## Earlier Tasks
`FRONTEND-001` (Persian RTL MVP interface), `MODEL-003` (AvalAI integration, superseded by
`MODEL-004`), `MODEL-002`, `MODEL-001`, `BACKEND-001`, `FIX-002`/`FIX-001`, and `SETUP-001` are
recorded in `progress.md`.
