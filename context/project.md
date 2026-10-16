# Project: Persian Writing Assistant

## Goal
Build an AI-powered Persian proofreading service that corrects spelling, grammar, punctuation, spacing, and typography while preserving the author's meaning and tone.

## Target Users
Persian-speaking users writing everyday, academic, and professional text.

## Product Versions

### V1 — MVP
Build a responsive Persian RTL website that:
- Accepts Persian text up to 1000 characters.
- Sends the text to a backend correction API.
- Uses external LLM APIs (Groq primary, Google Gemini automatic fallback) and a dedicated
  proofreading prompt.
- Displays the corrected Persian text.
- Supports copying the result.
- Handles invalid input and service failures clearly.
- Asks for explicit consent before any request, for the optional storage of the original and
  corrected text used to evaluate correction quality.

### V2 — Multiple LLM Providers
Add multiple LLM providers and controlled fallback when the primary provider encounters eligible failures.
Requested early: the Groq-to-Gemini fallback was implemented as `FALLBACK-001` during V1 at the
user's explicit request (see `task-plan.md` and `progress.md`).

### V3 — Telegram Bot
Build a Telegram bot that uses the existing backend correction API.

## Constraints
- All implementation is performed by coding agents.
- Implement and verify one task at a time.
- Prefer free LLM API tiers where available.
- Do not train a model from scratch.
- Do not introduce paid services or deploy without user approval.
- Protect API keys and user data.
- Do not persist submitted text by default. The only exception is the optional evaluation log
  (`correction-logging.md`), written per request and only with explicit user consent; a declined
  request stores neither the submitted nor the corrected text.
- The maximum text length must be configurable through backend environment settings.

## Success Criteria
V1 is complete when the website, backend, and LLM integration (with the Groq-to-Gemini fallback)
work together and the acceptance tests pass.

V2 and V3 must be implemented only after the preceding version is verified complete.

See `task-plan.md` for phase order and completion criteria.