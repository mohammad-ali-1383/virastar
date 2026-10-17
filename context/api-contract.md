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
Every error — validation, unknown route, unsupported method, provider failure, and unexpected
failure — uses one JSON structure with `Content-Type: application/json`.

    {
      "error": "TEXT_TOO_LONG",
      "message": "متن واردشده بیش از حداکثر مجاز است."
    }

Exactly `error` and `message` are present. `error` is a stable machine code and `message` is a safe
Persian message. No `detail` field, stack trace, provider payload, internal exception text, or
credential is ever returned.

## Error Codes

| Code | HTTP Status | Meaning |
|---|---:|---|
| `INVALID_INPUT` | 400 | Missing, empty, malformed, or wrong-type input (including a non-boolean consent flag) |
| `TEXT_TOO_LONG` | 400 | Text exceeds the configured limit |
| `NOT_FOUND` | 404 | Unknown route |
| `METHOD_NOT_ALLOWED` | 405 | Method not supported by the route |
| `INTERNAL_ERROR` | 500 | Unexpected internal error |
| `PROVIDER_UNAVAILABLE` | 503 | No provider produced a usable correction |
| `HTTP_ERROR` | original framework status | Any other framework-level HTTP error, same envelope |

Provider-specific classifications — rate/quota limit, authentication, timeout, connection failure,
server error, and unusable response — are **internal** to the adapters and correction service. The
endpoint never returns `429`, `502`, or `504`: every provider failure is reported as the single
`503 PROVIDER_UNAVAILABLE` (see Provider Error Mapping). Client-level rate limiting is not
implemented in V1, so the API itself has no rate-limit response. FastAPI's default `422` is also
never returned; validation failures are `400 INVALID_INPUT` or `400 TEXT_TOO_LONG`.

## Validation
- `text` must be a non-empty string after trimming.
- The maximum text length defaults to 1000 characters and must be configurable.
- `store_for_evaluation` must be a JSON boolean when present; any other type is invalid input.
- Reject malformed JSON and invalid input.
- Validate the length in the backend; frontend validation is only for user experience.
- Use a consistent error structure.
- Validation failures are `400 INVALID_INPUT` (or `400 TEXT_TOO_LONG`); FastAPI's default `422`
  response is replaced and never returned.
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
- The same generic `503` is used for every provider failure category (quota/rate limit,
  authentication, timeout, connection failure, server error, and unusable response).
- Unknown routes and unsupported methods use the same error structure: `404 NOT_FOUND` and
  `405 METHOD_NOT_ALLOWED` (the framework's `Allow` header is preserved on `405`).
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
- Every error keeps the `{error, message}` envelope, including `404` and `405`, so clients can
  handle failures uniformly.## Provider Error Mapping
Map known provider errors to the internal classifications in the adapters (quota/rate limit,
authentication, timeout, connection failure, server error, unusable response). Those
classifications drive the fallback decision and the sanitized server log; raw provider messages are
never exposed to clients.

The public mapping is deliberately single: whichever classification was raised and whichever
provider failed, the endpoint returns `503 PROVIDER_UNAVAILABLE` with the documented generic
message unless one provider produced a usable correction. The provider-specific codes
(`PROVIDER_RATE_LIMIT`, `PROVIDER_AUTH_ERROR`, `PROVIDER_TIMEOUT`) are therefore internal and are
never returned as `429`, `502`, or `504`.
