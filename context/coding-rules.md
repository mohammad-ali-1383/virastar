# Coding Rules

## General
- Follow `project.md`, `architecture.md`, and the relevant specifications.
- Implement only the current approved task.
- Inspect existing files before modifying them.
- Prefer simple, maintainable solutions.
- Do not implement V2 or V3 during V1.

## Code Quality
- Use clear names, small functions, and single-responsibility modules.
- Use TypeScript types and Python type hints.
- Keep frontend, API, correction logic, and provider-specific code separate.
- Avoid duplicated logic and unnecessary dependencies.

## Security
- Never hardcode API keys or secrets.
- Read secrets from backend environment variables or a secrets manager.
- Keep `.env` out of Git and provide a sanitized `.env.example`.
- Never expose credentials in frontend code, browser responses, logs, or documentation.
- Validate user input and enforce the configured text-length limit in the backend.
- Do not log full user text unless explicitly approved.
- Do not persist submitted text by default.

## LLM Integration
- Follow the selected provider's official API documentation.
- Verify the model identifier and access before integration.
- Keep provider configuration separate from correction logic.
- Set request timeouts.
- Handle authentication errors, rate limits, timeouts, and malformed responses explicitly.
- Never fabricate corrected text when the provider fails.

## Testing
- Add tests for new functionality.
- Mock LLM calls in routine automated tests.
- Avoid unnecessary real API calls and usage charges.
- Follow `testing.md`.

## Docker
- Use Docker Compose for local application services.
- Do not expose secrets in image layers or container logs.
- Do not mount unnecessary host directories into containers.
- Do not grant privileged container access without approval.

## Agent Workflow
- Read `current-task.md` and `progress.md` before starting.
- Work on one task at a time.
- Update task and progress records after verified work.
- Report changed files, tests, results, and known issues.
- Ask for approval before paid usage, deployment, destructive changes, or scope expansion.