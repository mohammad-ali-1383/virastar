# ویراستار متن فارسی — Persian Writing Assistant

AI-powered Persian proofreading service (spelling, grammar, punctuation, spacing, and
typography) that preserves the author's meaning and tone.

**Current status:** Phase 3 — the backend exposes `POST /api/v1/correct` (validation and the
documented response/error formats) and is backed by a real Google Gemini adapter
(`gemini-3.8-flash`). There is no product UI yet. See `context/current-task.md`.

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
│   │   └── services/        # correction service, prompt, and Gemini adapter
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
(default `1000`). The backend sends the fixed proofreading prompt as the Gemini system
instruction and the user's text separately, and returns the model's corrected text. If the
provider fails, the endpoint returns the matching documented error and never fabricates text.

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
| `GEMINI_API_KEY` | backend | *(empty)* | Google Gemini API key (secret); required for corrections |
| `GEMINI_MODEL` | backend | `gemini-3.8-flash` | Gemini model ID (stable, free-tier Flash text model) |
| `GEMINI_API_BASE_URL` | backend | `https://generativelanguage.googleapis.com` | Gemini Developer API base URL |
| `GEMINI_TIMEOUT_SECONDS` | backend | `30` | Per-request provider timeout |
| `VITE_API_BASE_URL` | frontend | `http://localhost:8000` | Backend base URL used by the browser |

Secrets live only in backend environment variables. Never place credentials in frontend
code or in `.env` files that are committed. The API key is sent to Gemini in the
`x-goog-api-key` request header (never the URL) and is never logged or returned.

## Local integration check (live Gemini)

The automated tests mock the provider and need no key. To exercise the real integration:

1. Get a free key from Google AI Studio: https://aistudio.google.com/apikey
2. Put it in `<repo root>/.env` (git-ignored) — never in source, chat, or a committed file:

   ```bash
   GEMINI_API_KEY=your-key-here
   GEMINI_MODEL=gemini-3.8-flash
   ```

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

   A corrected `{"corrected_text": "..."}` means the key, model, and endpoint are working.
   `502 PROVIDER_AUTH_ERROR` means the key is missing or rejected; `503`/`504`/`429` map to the
   documented provider errors. If `GEMINI_API_KEY` is empty, the endpoint fails with
   `502 PROVIDER_AUTH_ERROR` rather than returning the text unchanged.

   Confirm the loaded configuration without exposing the key:

   ```bash
   # Local
   cd backend && python -c "from app.config import settings; print(settings.gemini_model, bool(settings.gemini_api_key.get_secret_value()))"
   # Compose
   docker compose exec backend python -c "from app.config import settings; print(settings.gemini_model, bool(settings.gemini_api_key.get_secret_value()))"
   ```

   Both print the model ID followed by `True` when a key is present (never the key itself).

## Roadmap

Phases 2 and 3 add `POST /api/v1/correct` and the Google Gemini integration; later phases add the
website, and (in V2/V3) fallback providers and a Telegram bot. See `context/task-plan.md`.
