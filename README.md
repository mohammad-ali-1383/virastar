# ویراستار متن فارسی — Persian Writing Assistant

AI-powered Persian proofreading service (spelling, grammar, punctuation, spacing, and
typography) that preserves the author's meaning and tone.

**Current status:** Phases 3 and 4 — the backend exposes `POST /api/v1/correct` (validation and the
documented response/error formats) behind two selectable provider adapters, **Groq** and
**Google Gemini**, and the Persian RTL website calls that endpoint. See `context/current-task.md`.

## Project structure

```
.
├── backend/                 # Python 3.12+ / FastAPI service
│   ├── app/
│   │   ├── config.py        # environment-driven settings
│   │   ├── errors.py        # error codes, exceptions, FastAPI handlers
│   │   ├── schemas.py       # request/response models
│   │   ├── main.py          # FastAPI app (health + correction router)
│   │   ├── routers/         # HTTP endpoints
│   │   └── services/        # correction service, prompt, and the Groq/Gemini adapters
│   ├── tests/               # pytest suite (provider calls are stubbed)
│   ├── Dockerfile
│   ├── requirements.txt     # runtime dependencies (pinned)
│   └── requirements-dev.txt # test dependencies (pinned)
├── frontend/                # React + TypeScript + Vite app
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml       # local development stack
├── .env.example             # sanitized environment template
└── context/                 # project specifications
```

## Prerequisites

- Node.js 20.19+ or 22.12+ (Node 24 recommended)
- Python 3.12+
- Docker with the Compose plugin (optional, for containerized development)

## Setup

Copy the environment template. `.env` is git-ignored — never commit real credentials.

```bash
cp .env.example .env
```

### Environment file locations

A single `.env` at the **repository root** configures the backend in both workflows below. The
loader resolves its env files relative to the backend package, not the current directory, so
`cd backend && uvicorn ...` reads the same root file that Docker Compose does. `backend/.env`
is still honored and overrides the root file if you prefer to keep a local copy.

| Workflow | `.env` location | How it is loaded |
|---|---|---|
| Docker Compose | `<repo root>/.env` | `docker-compose.yml` → `env_file: .env` |
| Local Uvicorn (`cd backend`) | `<repo root>/.env` (or `backend/.env`) | `backend/app/config.py` reads both |

Real environment variables always win over `.env` values, so a platform-provided secret (for
example in production) is never overridden by a stray file.

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Option B — run services locally

Backend:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); use .venv/bin/activate on Linux/macOS
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (in a second terminal):

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## API

`POST /api/v1/correct` accepts `{"text": "..."}` and returns `{"corrected_text": "..."}`.
Errors use `{"error": "CODE", "message": "..."}` with the codes and statuses listed in
`context/api-contract.md`.

```bash
curl -X POST http://localhost:8000/api/v1/correct \
  -H "Content-Type: application/json" \
  -d '{"text": "متن فارسی"}'
```

The text is validated in the backend; the maximum length comes from `MAX_TEXT_LENGTH`
(default `1000`). The backend sends the fixed proofreading prompt to the provider named by
`CORRECTION_PROVIDER` as its system instruction, sends the user's text as a separate input, and
returns the model's corrected text. If the provider fails, the endpoint returns the matching
documented error and never fabricates text. The browser never learns which provider is active.

## Validation

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run build      # TypeScript type check + production build
cd frontend && npm run typecheck
```

## Configuration

| Variable | Scope | Default | Purpose |
|---|---|---|---|
| `APP_ENV` | backend | `development` | Runtime environment name |
| `MAX_TEXT_LENGTH` | backend | `1000` | Maximum accepted text length |
| `CORS_ORIGINS` | backend | dev origins | JSON array of allowed browser origins |
| `CORRECTION_PROVIDER` | backend | `groq` | Active provider: `groq` or `gemini` (no fallback) |
| `GROQ_API_KEY` | backend | *(empty)* | Groq API key (secret); required when Groq is selected |
| `GROQ_MODEL` | backend | `openai/gpt-oss-20b` | Groq model ID |
| `GROQ_TIMEOUT_SECONDS` | backend | `30` | Per-request Groq timeout |
| `GEMINI_API_KEY` | backend | *(empty)* | Gemini API key (secret); required when Gemini is selected |
| `GEMINI_MODEL` | backend | `gemini-3.5-flash-lite` | Gemini model ID |
| `GEMINI_TIMEOUT_SECONDS` | backend | `30` | Per-request Gemini timeout |
| `VITE_API_BASE_URL` | frontend | `http://localhost:8000` | Backend base URL used by the browser |

Secrets live only in backend environment variables. Never place credentials in frontend
code or in `.env` files that are committed. Each key is sent to its provider in a request header
— Groq in `Authorization: Bearer`, Gemini in `x-goog-api-key` (never the URL) — and is never
logged or returned. Only the selected provider's key is sent; the other key is never used.

## Local integration check (live provider)

The automated tests mock both providers, need no key, and never make a real API call. To exercise a
real integration, run one provider at a time; no live connection is verified until an actual API
request succeeds.

1. Get a key:
   - Groq — https://console.groq.com/keys
   - Google Gemini — https://aistudio.google.com/apikey
2. Put it in `<repo root>/.env` (git-ignored) — never in source, chat, or a committed file. Only the
   selected provider's key is used:

   ```bash
   # Option 1 — Groq (default provider)
   CORRECTION_PROVIDER=groq
   GROQ_API_KEY=your-key-here
   GROQ_MODEL=openai/gpt-oss-20b

   # Option 2 — Google Gemini (use instead of the Groq lines above)
   # CORRECTION_PROVIDER=gemini
   # GEMINI_API_KEY=your-key-here
   # GEMINI_MODEL=gemini-3.5-flash-lite
   ```

   `CORRECTION_PROVIDER` must be exactly `groq` or `gemini`. Any other value fails every request
   with `500 INTERNAL_ERROR` and calls no provider — the selection never falls back silently.

3. Start the backend — pick one workflow:

   Local Uvicorn:

   ```bash
   cd backend && uvicorn app.main:app --reload --port 8000
   ```

   Docker Compose (from the repository root). A changed `.env` is only picked up when the
   container is recreated, so use `up` rather than `restart`; `--force-recreate` guarantees it.
   No image rebuild is needed for a `.env` edit, and none is needed for application code
   changes either, because `./backend/app` is bind-mounted with `--reload`:

   ```bash
   docker compose up -d --force-recreate backend
   # add --build only if backend/requirements*.txt or the Dockerfile changed
   ```

4. Send a real request and check the result:

   ```bash
   curl -X POST http://localhost:8000/api/v1/correct \
     -H "Content-Type: application/json" \
     -d '{"text": "سلام این یک متن ازمایشی است"}'
   ```

   A corrected `{"corrected_text": "..."}` means the key, model, and endpoint work for the selected
   provider. `502 PROVIDER_AUTH_ERROR` means the selected key is missing or rejected;
   `503`/`504`/`429` map to the documented provider errors. If the selected provider's key is empty,
   the endpoint fails with `502 PROVIDER_AUTH_ERROR` rather than returning the text unchanged.

   Repeat step 4 once per provider after switching `CORRECTION_PROVIDER` and restarting the backend
   (recreate the container for Compose).

   Confirm the loaded configuration without exposing the key:

   ```bash
   # Local
   cd backend && python -c "from app.config import settings; p = settings.correction_provider; print(p, getattr(settings, f'{p}_model'), bool(getattr(settings, f'{p}_api_key').get_secret_value()))"
   # Compose
   docker compose exec backend python -c "from app.config import settings; p = settings.correction_provider; print(p, getattr(settings, f'{p}_model'), bool(getattr(settings, f'{p}_api_key').get_secret_value()))"
   ```

   Both print the active provider, its model ID, and `True` when its key is present (never the key
   itself).

## Roadmap

Phase 2 adds `POST /api/v1/correct`, Phase 3 the selectable Groq/Gemini provider adapters, and
Phase 4 the website. V2/V3 add controlled fallback and a Telegram bot. See `context/task-plan.md`.
