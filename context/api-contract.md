# API Contract

## Endpoint
`POST /api/v1/correct`

## Request
Content-Type: `application/json`

    {
      "text": "متن فارسی مورد نظر برای اصلاح",
      "store_for_evaluation": false
    }

### Consent field (`store_for_evaluation`)
- Optional JSON boolean, default `false` (`correction-logging.md`).
- `true` — the backend may append the submitted and corrected text to the evaluation log so the
  prompt and providers can be reviewed.
- `false` or omitted — neither text is stored for evaluation.
- Must be a real JSON boolean. A string (`"true"`, `"yes"`) or a number is `400 INVALID_INPUT`,
  never an accidental opt-in.
- The backend enforces this; the frontend only reports the user's choice.

## Success Response
HTTP `200 OK`

    {
      "corrected_text": "متن اصلاح‌شده فارسی"
    }

## Error Response
All errors must use a consistent JSON structure.

    {
      "error": "TEXT_TOO_LONG",
      "message": "متن واردشده بیش از حداکثر مجاز است."
    }

## Error Codes

| Code | HTTP Status | Meaning |
|---|---:|---|
| `INVALID_INPUT` | 400 | Missing, empty, or invalid text |
| `TEXT_TOO_LONG` | 400 | Text exceeds the configured limit |
| `PROVIDER_UNAVAILABLE` | 503 | LLM provider is unavailable |
| `PROVIDER_TIMEOUT` | 504 | LLM request timed out |
| `PROVIDER_RATE_LIMIT` | 429 | Provider rate or quota limit reached |
| `PROVIDER_AUTH_ERROR` | 502 | Provider authentication failed |
| `INTERNAL_ERROR` | 500 | Unexpected internal error |

## Validation
- `text` must be a non-empty string after trimming.
- The maximum text length defaults to 1000 characters and must be configurable.
- `store_for_evaluation` must be a JSON boolean when present; any other type is invalid input.
- Reject malformed JSON and invalid input.
- Validate the length in the backend; frontend validation is only for user experience.
- Use a consistent error structure.
- Never expose stack traces, API keys, credentials, or raw internal provider errors.

## Behavior
- The frontend sends text only to this backend endpoint.
- The backend validates input and invokes the correction service.
- Validation errors (missing/empty/whitespace text, and text over the limit) are returned without
  calling any LLM provider.
- The correction service always tries Groq first and retries the same request once with Gemini when
  Groq fails for a provider-related reason (quota/rate limit, authentication/configuration, timeout,
  connection failure, server error, or an invalid/empty response).
- Return HTTP 200 only when correction succeeds, using the text of whichever provider succeeded.
- When both providers fail, return `503 PROVIDER_UNAVAILABLE` with the generic message: the client
  is never told which provider failed or why.
- Never fabricate corrected text when the provider fails.
- Only a successful correction can be stored for evaluation, and only when the request consented:
  the record names the provider and model that actually succeeded, so a Groq-to-Gemini fallback is
  recorded as Gemini.
- A failed evaluation-log write never changes the response: the client still receives its correction.
  See `correction-logging.md`.

## Compatibility
- Keep the public endpoint and response format stable in V2.
- The Telegram bot in V3 must use the same backend API.
- Clients must not need to know which provider is active.

## Provider Error Mapping
Map known provider errors to the public error codes above. Do not expose raw provider error messages to clients. Use `PROVIDER_RATE_LIMIT` only when the provider's rate/quota limit is identified; use `429` for that public error.

The per-provider mapping stays in the adapters (an exhaustion, authentication, timeout, or server error raises the matching internal error). Because the endpoint retries once with the fallback provider and returns `PROVIDER_UNAVAILABLE` when both attempts fail, the provider-specific codes below are not what a client normally sees: the successful provider's correction is returned, or the single generic `503`.