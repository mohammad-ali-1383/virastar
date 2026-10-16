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
- Evaluate Google Gemini API as the initial candidate.
- Verify the model identifier, API availability, free-tier eligibility, and Persian proofreading quality.
- Report findings before switching providers or models.
- Implement the selected provider adapter and `correction-prompt.md`.
- Add timeout and provider-error handling.

### Phase 4: Website
- Build the interface according to `ui.md`.
- Connect the frontend to the backend.
- Implement the character counter, input, loading, result, copy, and error states.

### Phase 5: Integration and Acceptance
- Run backend, frontend, and integration checks.
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

## V3 — Telegram Bot
Start only after V2 is accepted.
- Create/configure the bot using Telegram BotFather.
- Implement message handling and connect the bot to the existing backend.
- Handle invalid input, long messages, and service failures.
- Test the complete Telegram flow.

## Scope Control
Do not implement future-version features early. If an architectural change or model replacement is required, explain why and request approval before expanding scope.