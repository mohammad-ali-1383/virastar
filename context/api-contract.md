# API Contract

## Endpoint
`POST /api/v1/correct`

## Request
Content-Type: `application/json`

    {
      "text": "متن فارسی مورد نظر برای اصلاح"
    }

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
- Reject malformed JSON and invalid input.
- Validate the length in the backend; frontend validation is only for user experience.
- Use a consistent error structure.
- Never expose stack traces, API keys, credentials, or raw internal provider errors.

## Behavior
- The frontend sends text only to this backend endpoint.
- The backend validates input and invokes the correction service.
- The correction service uses the configured LLM adapter.
- Return HTTP 200 only when correction succeeds.
- Never fabricate corrected text when the provider fails.

## Compatibility
- Keep the public endpoint and response format stable in V2.
- The Telegram bot in V3 must use the same backend API.
- Clients must not need to know which provider is active.

## Provider Error Mapping
Map known provider errors to the public error codes above. Do not expose raw provider error messages to clients. Use `PROVIDER_RATE_LIMIT` only when the provider's rate/quota limit is identified; use `429` for that public error.