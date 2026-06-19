# Data Export and Privacy Requests

## Overview
This article covers how customers can export their data and how privacy-related requests (such as data deletion under GDPR/CCPA) are handled.

## Exporting Account Data
1. Navigate to **Account Settings > Data & Privacy > Export Data**.
2. Select the data categories to include (Projects, Messages, Billing History, Usage Logs).
3. Click **Request Export**. The export is generated asynchronously and a download link is emailed within 24 hours.
4. Export download links expire after 72 hours for security; a new export must be requested if missed.

## Supported Export Formats
- JSON (default, includes full nested data structure)
- CSV (flattened, available for Projects and Billing History only)

## Data Deletion Requests (Right to be Forgotten)
Customers based in regions covered by GDPR or CCPA can request full account data deletion.
1. Submit the request via **Account Settings > Data & Privacy > Delete My Data**, or by emailing privacy@ourapp.com.
2. Identity verification is required before processing (matching email + a confirmation step).
3. Deletion is processed within 30 days as required by law.
4. Some data may be retained longer where required for legal/tax compliance (e.g., billing records retained for 7 years per financial regulations), but this data is anonymized where possible.

## Data Portability
Exported JSON data follows our published schema (available in API docs) and can be used to migrate to another platform. We do not provide direct migration tooling to competitor platforms.

## When to Escalate
Escalate when: a data deletion request needs expedited processing due to legal requirements, when a customer disputes what data is being retained, or when an export repeatedly fails to generate after 48 hours.
