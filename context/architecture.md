# System Architecture

## 1. V1 Components
1. **Frontend:** React website with Persian RTL layout.
2. **Backend API:** FastAPI service that validates requests and coordinates correction.
3. **Correction Service:** Applies the fixed proofreading prompt and manages the correction workflow.
4. **LLM Adapter:** Communicates with one configured external LLM API.

The frontend must never call the LLM provider directly.

## 2. Request Flow
1. The user enters Persian text and submits it.
2. The frontend sends the text to the backend API.
3. The backend validates the input and enforces the configured maximum length.
4. The correction service combines the fixed system prompt from `correction-prompt.md` with the user's text as a separate input.
5. The LLM adapter sends the request to the configured provider.
6. The backend validates the provider response and returns the corrected text.
7. The frontend displays the result or a safe error message.

## 3. Component Boundaries
- **Frontend:** UI, input handling, character counter, loading states, and result display.
- **Backend API:** Request validation and HTTP response handling.
- **Correction service:** Proofreading workflow and prompt management.
- **LLM adapter:** Provider-specific authentication, requests, and response parsing.
- **Configuration:** Model settings, endpoints, timeouts, maximum text length, and secrets.

## 4. Development Origins
- Frontend: `http://localhost:5173`
- Frontend alternative: `http://127.0.0.1:5173`
- Backend: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

Allow only the specified frontend development origins in development CORS settings.

## 5. Future Versions
- **V2:** Add independent provider adapters, controlled fallback, bounded retries, and provider-specific error handling.
- **V3:** Add a Telegram bot that uses the existing backend API. Do not duplicate correction logic.

Do not implement V2 or V3 during V1.

## 6. Security and Reliability
- Keep API keys on the backend.
- Read secrets from environment variables or a secrets manager.
- Validate input and enforce a configurable maximum length.
- Use request timeouts and safe error responses.
- Do not store user text by default.
- Never fabricate a correction when the LLM request fails.

## 7. Related Specifications
- Technology choices: `tech-stack.md`
- API request and response: `api-contract.md`
- Coding constraints: `coding-rules.md`
- Prompt: `correction-prompt.md`
- UI: `ui.md`
- Testing: `testing.md`
- Implementation order: `task-plan.md`