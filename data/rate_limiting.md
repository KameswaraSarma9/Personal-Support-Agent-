# Rate Limiting and Performance

## Overview
This article explains API rate limits, how to handle 429 responses, and general performance troubleshooting.

## Rate Limit Tiers
| Plan | Requests/Minute | Burst Allowance |
|------|-----------------|------------------|
| Free | 20 | 5 |
| Standard | 100 | 20 |
| Pro | 1000 | 100 |
| Enterprise | Custom | Custom |

## Reading Rate Limit Headers
Every API response includes the following headers:
- `X-RateLimit-Limit`: total requests allowed in the current window
- `X-RateLimit-Remaining`: requests remaining in the current window
- `X-RateLimit-Reset`: Unix timestamp when the window resets

## Handling 429 Too Many Requests
When you receive a 429 response, the `Retry-After` header indicates how many seconds to wait before retrying. Implement exponential backoff with jitter rather than retrying immediately, as immediate retries can compound the problem.

```python
import time, random

def call_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
    raise Exception("Max retries exceeded")
```

## Slow API Response Times
If response times exceed 2 seconds consistently:
1. Check **Status Page** for any ongoing incidents.
2. Confirm requests are not being made from a region far from our primary data center (US-East). Consider using the EU endpoint if your traffic originates from Europe.
3. Large payload requests (bulk operations over 1000 records) are inherently slower; consider pagination.

## Burst Traffic and Temporary Limit Increases
Temporary rate limit increases for planned traffic spikes (e.g., a product launch) can be requested by contacting support at least 48 hours in advance.

## When to Escalate
Escalate when: rate limit headers show available quota but requests still return 429, when response times remain abnormally slow after ruling out the above causes, or for urgent temporary limit increase requests with less than 48 hours notice.
