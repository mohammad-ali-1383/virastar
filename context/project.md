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
- Uses one external LLM API and a dedicated proofreading prompt.
- Displays the corrected Persian text.
- Supports copying the result.
- Handles invalid input and service failures clearly.

### V2 — Multiple LLM Providers
Add multiple LLM providers and controlled fallback when the primary provider encounters eligible failures.

### V3 — Telegram Bot
Build a Telegram bot that uses the existing backend correction API.

## Constraints
- All implementation is performed by coding agents.
- Implement and verify one task at a time.
- Prefer free LLM API tiers where available.
- Do not train a model from scratch.
- Do not introduce paid services or deploy without user approval.
- Protect API keys and user data.
- Do not persist submitted text by default.
- The maximum text length must be configurable through backend environment settings.

## Success Criteria
V1 is complete when the website, backend, and single-provider LLM integration work together and the acceptance tests pass.

V2 and V3 must be implemented only after the preceding version is verified complete.

See `task-plan.md` for phase order and completion criteria.