# Correction Logging (Optional, Consent-Based)

## Purpose
Keep a small, optional record of real corrections so the proofreading prompt and the provider
fallback can be evaluated later (correction quality, which provider answered, which model). Storage
happens **only** with the user's explicit consent; it is never a requirement for getting a
correction.

## Consent
- The website shows a Persian dialog after «اصلاح متن» is pressed and before any request is sent
  (`ui.md` -> Privacy and consent). Both choices run the correction.
- The request carries the choice explicitly as `store_for_evaluation`
  (`api-contract.md` -> Request). `true` consents to storage, `false` declines.
- The field is optional and defaults to `false`: a client that states no choice stores nothing. Only
  a real JSON boolean counts — a string such as `"yes"` or the number `1` is rejected as
  `400 INVALID_INPUT` rather than treated as consent.
- **The backend enforces this.** The frontend only collects the choice; `POST /api/v1/correct`
  decides whether anything is written.
- If the dialog is dismissed (Escape, backdrop, close button) no request is sent at all.

## Record
One JSON Lines row per **successful** correction, appended to `CORRECTION_LOG_PATH`
(default `<repository root>/logs/corrections.jsonl`):

    {"timestamp":"2026-10-16T12:30:00+00:00","original_text":"...","provider":"gemini","model":"gemini-3.5-flash-lite","corrected_text":"..."}

| Field | Meaning |
|---|---|
| `timestamp` | When the record was written, ISO 8601 with a UTC offset. |
| `original_text` | The submitted text after the documented trimming. |
| `provider` | The provider that **actually succeeded**: `groq`, or `gemini` when the fallback produced the correction. |
| `model` | The model ID the successful adapter sent (`GROQ_MODEL` or `GEMINI_MODEL`). |
| `corrected_text` | The final corrected text returned to the client. |

Rows are decoded with `ensure_ascii=False`, so Persian is stored readably. The record is written
only after a successful correction: failed requests, validation errors, and provider failures produce
no record.

## Declined requests
- Neither the original nor the corrected text is written anywhere — the log file is not even created.
- Nothing about the declined request reaches the application logs either (only the documented error
  codes and metadata are ever logged).

## Failures
- A failed write (unwritable path, missing permissions) never fails the request and never retries it:
  the endpoint still returns `200` with the corrected text, because the correction did succeed.
- The failure is reported as a sanitized `WARNING` naming the exception class and the configured
  path only. The text being corrected never enters the application log.

## Security Rules
- Never log API keys, authorization headers, provider response bodies, or user text (the consented
  evaluation record is the single, deliberate exception).
- `logs/` is git-ignored; no record file is ever committed.
- The path always comes from configuration, never from a request.
- Records are appended, never rewritten or truncated.

## Implementation Rules
- The store lives in `backend/app/services/correction_log.py`; the endpoint is the only caller and
  the only place consent is evaluated.
- Provider and model come from the adapter that succeeded (`CorrectionResult`), so a Groq-to-Gemini
  fallback records Gemini and the Gemini model.
- `CORRECTION_LOG_PATH` is configuration (`config.py`); tests point it at a temporary file.
- Rows are single `append`-mode writes; the store does not deduplicate or rewrite existing records.
