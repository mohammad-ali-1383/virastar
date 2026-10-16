# Testing Strategy

## General
- Test each task before marking it complete.
- Use automated tests where practical.
- Mock external LLM calls in routine tests.
- Avoid unnecessary API usage and charges.

## Backend Tests
- Valid Persian text returns a non-empty `corrected_text`.
- Missing, empty, whitespace-only, and malformed requests are rejected.
- A text of exactly 1000 characters is accepted if otherwise valid.
- A text of 1001 characters is rejected with `TEXT_TOO_LONG`.
- The configured limit can be changed through backend configuration.
- Provider timeouts, authentication errors, rate limits, and server errors map to the documented error codes.
- Invalid or empty provider responses do not produce false success.
- Responses follow `api-contract.md`.

## Frontend Tests
- Users can enter and submit Persian text.
- The character counter updates correctly.
- The UI communicates the 1000-character limit.
- Loading, success, validation-error, and service-error states work correctly.
- The corrected text is displayed without replacing the original input.
- Copying the result works.
- RTL layout and common desktop/mobile screen sizes are supported.
- Backend failures do not crash the interface.

## Correction Quality
Maintain a small Persian test set covering:
- Spelling and grammatical errors.
- Persian punctuation and spacing.
- Half-spaces and typography.
- Informal and formal writing.
- Text that is already correct.
- Names, numbers, and URLs.
- Long sentences and ambiguous wording.

Verify that corrections preserve the original meaning, tone, and information. Avoid unnecessary rewriting.

## MVP Acceptance
V1 passes when:
- Backend and frontend tests pass.
- The website communicates with the backend.
- A real request to the configured LLM API returns a usable correction.
- Failure scenarios display safe, understandable errors.
- No credentials are exposed.
- The text is not persisted by default.

Record verified results in `progress.md`.