# Database Integration & Internal Errors

## Overview
This article addresses internal server errors (HTTP 500) related to our database integration connector, used for syncing customer data with external databases (PostgreSQL, MySQL, MongoDB).

## Symptom: Intermittent 500 Errors During Sync
This typically indicates a connection pool exhaustion issue. Each integration is allotted a maximum of 20 concurrent connections. When sync jobs overlap (e.g., a scheduled sync starting before the previous one finishes), the pool can be exhausted, causing new connections to fail.

### Resolution Steps
1. Check the **Integrations > Sync Logs** panel for "Connection Pool Exhausted" warnings.
2. Reduce sync frequency from real-time to a 5-minute interval under Integration Settings.
3. If using a self-hosted database, confirm your database server's `max_connections` setting is at least 25 to accommodate our pool plus buffer.

## Symptom: Sync Fails Immediately with "Schema Mismatch" Error
This occurs when the destination table's schema does not match the expected field types. Common case: a field that was previously `VARCHAR` was changed to `INT` outside of our system, breaking the mapping.

### Resolution Steps
1. Go to **Integrations > Field Mapping** and click "Re-validate Schema."
2. Manually remap any fields flagged in red.
3. If the issue persists, delete and recreate the field mapping entirely (this does not affect already-synced historical data).

## Symptom: Internal Error Code DB-4471
This specific error code indicates a timeout while writing to the destination database, usually caused by large batch sizes. Default batch size is 500 records.

### Resolution Steps
1. Reduce batch size to 100 under **Integration Settings > Advanced > Batch Size**.
2. Confirm the destination database is not under heavy load from other processes during the sync window.

## Logging and Diagnostics
Full sync logs, including request/response payloads for failed records, are retained for 14 days and can be downloaded from **Integrations > Sync Logs > Export**.

## When to Escalate
Escalate when: error logs show a stack trace pointing to our internal infrastructure (not the customer's database), when the same error persists after all resolution steps, or when data integrity (e.g., partial writes, duplicate records) is suspected.
