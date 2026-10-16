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
- Use exactly one external LLM API.
- Evaluate Google Gemini API through Google AI Studio as the initial candidate.
- Candidate model: `gemini-3.8-flash`, subject to verification of the actual model identifier, API availability, free-tier eligibility, and Persian proofreading quality.
- Do not assume that free access or quotas are guaranteed.
- Keep provider-specific integration isolated for V2.

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