# API Authentication Troubleshooting

## Overview
This guide covers common authentication errors developers encounter when integrating with our REST API, including 401 and 403 errors.

## Authentication Method
Our API uses Bearer Token authentication. Every request must include the following header:

```
Authorization: Bearer <your_api_key>
```

API keys can be generated and revoked from the **Developer Settings > API Keys** panel in your dashboard. Each key is shown only once at creation time, so store it securely.

## Common Error: 401 Unauthorized
A 401 response means the request did not include valid credentials. Common causes:
- The `Authorization` header is missing entirely.
- The header is malformed (e.g., missing the word "Bearer" before the key, or extra whitespace).
- The API key has been revoked or regenerated, invalidating the old key.
- The API key was copied incorrectly (truncated or includes a trailing newline).

### Resolution Steps
1. Confirm the header format exactly matches: `Authorization: Bearer sk_live_xxxxxxxx`.
2. Regenerate a new API key from the dashboard and update your environment variables.
3. Check for trailing whitespace or newline characters when copying the key from `.env` files.
4. Verify the key has not expired — keys created under the legacy v1 system expire after 12 months.

## Common Error: 403 Forbidden
A 403 response means the credentials are valid but lack permission for the requested action. Common causes:
- The API key belongs to a read-only scope but is being used for a write operation (POST/PUT/DELETE).
- The account's subscription plan does not include access to the requested endpoint.
- IP allow-listing is enabled on the account and the request origin is not on the allow-list.

### Resolution Steps
1. Check the key's scope under Developer Settings — scopes are "Read Only," "Read/Write," or "Admin."
2. Confirm the endpoint is available on your current plan tier (some endpoints are Enterprise-only).
3. If IP allow-listing is enabled, add the server's outbound IP address to the allow-list.

## Rate Limiting
API requests are limited to 100 requests per minute per key on the Standard plan, and 1000 requests per minute on the Enterprise plan. Exceeding this returns a 429 status code with a `Retry-After` header indicating how many seconds to wait.

## Webhook Signature Verification Failures
If webhook signature verification fails, confirm you are using the signing secret from the **Webhooks** tab (not the API key) and that the raw request body is used for HMAC computation, not a parsed/re-serialized version.

## When to Escalate
Escalate to a human agent if: the customer's API key shows as valid in the dashboard but still returns 401 errors, or if there is suspected unauthorized API usage on the account.
