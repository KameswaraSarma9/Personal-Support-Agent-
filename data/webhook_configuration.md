# Webhook Configuration Guide

## Overview
Webhooks let your application receive real-time notifications when events occur in your account (e.g., payment succeeded, user created, sync completed).

## Setting Up a Webhook
1. Go to **Developer Settings > Webhooks > Add Endpoint**.
2. Enter your publicly accessible HTTPS endpoint URL. HTTP (non-TLS) endpoints are not supported.
3. Select which event types to subscribe to from the list (e.g., `payment.succeeded`, `user.created`, `sync.completed`).
4. Save the endpoint. A signing secret is generated immediately — store this securely, it is shown only once.

## Verifying Webhook Signatures
Every webhook request includes an `X-Signature` header containing an HMAC-SHA256 hash of the raw request body, signed with your endpoint's signing secret. Always verify this signature before processing the payload to prevent spoofed requests.

Common verification mistakes:
- Using the API key instead of the webhook signing secret.
- Verifying against a parsed/re-serialized JSON body instead of the raw bytes received.
- Trimming or modifying whitespace in the body before verification.

## Retry Behavior
If your endpoint does not respond with a 2xx status within 10 seconds, the webhook is retried with exponential backoff: 1 minute, 5 minutes, 30 minutes, 2 hours, then 12 hours. After 5 failed attempts, the webhook is marked as failed and will not retry further.

## Viewing Webhook Logs
**Developer Settings > Webhooks > [Endpoint] > Logs** shows the last 200 delivery attempts, including response codes and response bodies, useful for debugging.

## Replaying Failed Webhooks
Failed webhook events can be manually replayed from the Logs panel by clicking "Resend" next to any failed delivery, up to 30 days after the original event.

## When to Escalate
Escalate when: webhooks are consistently failing to deliver despite a confirmed-working endpoint (suggesting an infrastructure issue on our end), or when a customer needs historical events older than 30 days replayed.
