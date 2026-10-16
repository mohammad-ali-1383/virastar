# Implementation Plan

## Workflow
- Complete tasks in order.
- Work only on the active task in `current-task.md`.
- Verify each task before marking it complete.
- Use `testing.md` for acceptance criteria.
- Record verified results in `progress.md`.
- Do not begin the next phase until the current phase is accepted.

## V1 — MVP Website

### Phase 1: Project Setup
- Inspect the existing repository and project documentation.
- Create the minimal frontend and backend structures.
- Configure dependencies, Git, Docker, and environment files.
- Add concise setup and run instructions.
- Do not implement correction logic yet.

### Phase 2: Backend API
- Implement `POST /api/v1/correct`.
- Validate text and enforce the configurable maximum length.
- Implement consistent error responses.
- Add automated tests using mocked provider responses.

### Phase 3: LLM Selection and Integration
- Evaluate a candidate provider and verify the model identifier, API availability, free-tier eligibility, and Persian proofreading quality.
- Report findings before switching providers or models.
- Implement the selected provider adapter and `correction-prompt.md`.
- Add timeout and provider-error handling.
- Providers (V1): **Groq** (OpenAI-compatible Chat Completions, `GROQ_MODEL`, default
  `openai/gpt-oss-20b`), always tried first, and **Google Gemini** (`generateContent`,
  `GEMINI_MODEL`, default `gemini-3.5-flash-lite`) as the automatic fallback. Supersedes the
  explicit `CORRECTION_PROVIDER` selection of `MODEL-004`, the AvalAI integration (`MODEL-003`),
  and the first Gemini candidate (`MODEL-001`). See `tech-stack.md`.

### Phase 4: Website
- Build the interface according to `ui.md`.
- Connect the frontend to the backend.
- Implement the character counter, input, loading, result, copy, and error states.
- Ask for consent before sending a request and pass the explicit `store_for_evaluation` flag
  (`LOG-001`, `correction-logging.md`); the backend enforces whether anything is stored.

### Phase 5: Integration and Acceptance
- Run backend, frontend, and integration checks (backend suite, `npm run test`, `npm run build`).
- Test the Persian proofreading prompt with representative text.
- Fix blocking issues and verify the MVP acceptance criteria.

### Phase 6: Deployment
- Obtain user approval before deployment or paid usage.
- Configure production secrets securely.
- Deploy frontend and backend only after local verification.
- Verify the live application.

## V2 — Multiple LLM Providers
Start only after V1 is accepted.
- Add at least one independent fallback provider.
- Implement bounded fallback for eligible failures.
- Test provider failures and fallback behavior.
- Preserve the existing API contract.

Progress: the independent fallback provider, the bounded fallback (exactly one retry), and the
fallback test suite were implemented as `FALLBACK-001` at the user's explicit request before V1 was
accepted (Groq primary, Gemini fallback, `503 PROVIDER_UNAVAILABLE` when both fail).

## V3 — Telegram Bot
Start only after V2 is accepted.
- Create/configure the bot using Telegram BotFather.
- Implement message handling and connect the bot to the existing backend.
- Handle invalid input, long messages, and service failures.
- Test the complete Telegram flow.

## Scope Control
Do not implement future-version features early. If an architectural change or model replacement is required, explain why and request approval before expanding scope.