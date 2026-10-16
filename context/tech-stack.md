# Technology Stack

## Frontend
- React + TypeScript + Vite.
- Responsive Persian RTL interface.
- Use the native Fetch API unless another library is justified.
- Development port: `5173`.

## Backend
- Python 3.12+.
- FastAPI for HTTP endpoints.
- Pydantic for request and response validation.
- HTTPX for asynchronous LLM requests.
- Development port: `8000`.

## LLM Integration — V1
- Two provider adapters are supported and the active one is chosen explicitly with
  `CORRECTION_PROVIDER` (`groq` or `gemini`, default `groq`). There is no automatic fallback: an
  unrecognized value fails the request instead of silently calling another provider.
- Only the selected provider is called, and only its credential is sent. Keep both keys
  backend-only.
- **Groq** — OpenAI-compatible Chat Completions API.
  - Endpoint: `POST https://api.groq.com/openai/v1/chat/completions`.
  - Authentication: bearer API key from `GROQ_API_KEY`.
  - Model: `openai/gpt-oss-20b` by default, configurable through `GROQ_MODEL`.
- **Google Gemini** — `generateContent` method.
  - Endpoint:
    `POST https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent`.
  - Authentication: `x-goog-api-key` header with the key from `GEMINI_API_KEY`.
  - Model: `gemini-3.5-flash-lite` by default, configurable through `GEMINI_MODEL`.
- Per-request timeouts: `GROQ_TIMEOUT_SECONDS` and `GEMINI_TIMEOUT_SECONDS` (default `30`).
- Do not assume that free access or quotas are guaranteed.
- Keep provider-specific integration isolated behind the adapter interface so V2 can add
  fallback.

## Configuration and Secrets
- Store credentials in backend environment variables.
- Provide a sanitized `.env.example`.
- Exclude `.env` and other secret files from Git.
- Never expose credentials in frontend code, API responses, logs, or documentation.

## Development and Runtime
- Use Git for version control.
- Use Docker and Docker Compose for reproducible development and application runtime.
- Pin compatible dependency versions.
- Keep the Agent execution environment separate from the application's runtime containers where practical.

## Storage
- No database in V1.
- Do not persist submitted text by default.

## Deployment
- Consider suitable hosting after local verification.
- Obtain user approval before deployment or paid usage.
- Do not assume free hosting provides continuous availability.

## Future Versions
- V2: Multiple LLM providers and fallback.
- V3: Telegram bot using the existing backend.

Do not implement future-version features during V1.