# System Architecture

## 1. V1 Components
1. **Frontend:** React website with Persian RTL layout.
2. **Backend API:** FastAPI service that validates requests and coordinates correction.
3. **Correction Service:** Applies the fixed proofreading prompt and manages the correction workflow.
4. **LLM Adapter:** Communicates with an external LLM API. Two adapters are supported — Groq
   (always tried first) and Google Gemini (the automatic fallback). The order lives in the code,
   not in configuration.
5. **Evaluation log (optional):** Appends consented corrections to a JSON Lines file for later
   quality review (`correction-logging.md`). It is written only when the request asks for it and
   never for a declined request.

The frontend must never call the LLM provider directly.

## 2. Request Flow
1. The user enters Persian text and submits it, then chooses a consent option in the dialog
   (`ui.md`); dismissing it sends nothing.
2. The frontend sends the text and the explicit consent flag to the backend API.
3. The backend validates the input and enforces the configured maximum length.
4. The correction service combines the fixed system prompt from `correction-prompt.md` with the user's text as a separate input.
5. The LLM adapter sends the request to Groq. If that attempt fails for a provider-related
   reason (quota/rate limit, authentication/configuration, timeout, connection failure, server
   error, or an unusable response), the same request is sent once to Google Gemini.
6. The backend validates the response of the provider that succeeded and returns the corrected
   text; when both providers fail it returns the generic `PROVIDER_UNAVAILABLE` error.
7. If — and only if — the request consented, the backend appends one record naming that provider
   and its model, together with both texts.
8. The frontend displays the result or a safe error message.

## 3. Component Boundaries
- **Frontend:** UI, input handling, character counter, loading states, and result display.
- **Backend API:** Request validation and HTTP response handling.
- **Correction service:** Proofreading workflow and prompt management, including which provider
  and model produced a correction.
- **Evaluation log:** Consent-based, append-only JSON Lines store; the endpoint evaluates consent
  and the store owns file creation and the failure policy.
- **LLM adapter:** Provider-specific authentication, requests, and response parsing, one module
  per provider behind a shared interface. The correction service owns the retry order.
- **Configuration:** Model settings, endpoints, timeouts, maximum text length, and secrets.

## 4. Development Origins
- Frontend: `http://localhost:5173`
- Frontend alternative: `http://127.0.0.1:5173`
- Backend: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

Allow only the specified frontend development origins in development CORS settings.

## 5. Future Versions
- **V2:** Add independent provider adapters, bounded retries, and provider-specific error
  handling. Controlled fallback (Groq first, Gemini second) was implemented ahead of V2 as
  `FALLBACK-001` at the user's explicit request; there is exactly one fallback attempt.
- **V3:** Add a Telegram bot that uses the existing backend API. Do not duplicate correction logic.

Do not implement V2 or V3 during V1.

## 6. Security and Reliability
- Keep API keys on the backend.
- Read secrets from environment variables or a secrets manager.
- Validate input and enforce a configurable maximum length.
- Use request timeouts and safe error responses.
- Do not store user text by default.
- Never fabricate a correction when the LLM request fails.
- Send only the credential of the provider being called, and log provider names with sanitized
  error categories (never keys, user text, or provider response bodies).
- Store user text only with explicit per-request consent, in the dedicated evaluation log, which
  stays out of Git; a logging failure never breaks the correction.

## 7. Related Specifications
- Technology choices: `tech-stack.md`
- API request and response: `api-contract.md`
- Coding constraints: `coding-rules.md`
- Prompt: `correction-prompt.md`
- UI: `ui.md`
- Testing: `testing.md`
- Implementation order: `task-plan.md`