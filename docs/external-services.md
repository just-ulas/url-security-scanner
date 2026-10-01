# External services and access requirements

No external URL reputation service is currently integrated or called.

## Candidate providers (selection pending)

| Service | Purpose | Credentials/access needed | Data/privacy considerations |
|---|---|---|---|
| VirusTotal API v3 | URL/domain reputation and provider-attributed engine observations | User-provisioned API key with documented URL/report permissions and quota | Submitted URLs/identifiers are sent to VirusTotal; plan limits and sharing semantics must be reviewed before enabling |
| Google Safe Browsing Lookup API | Known unsafe URL lookup | Google Cloud project, enabled Safe Browsing API, API key, and applicable quota/billing configuration | Submitted URL is sent to Google; terms, attribution, quota, and privacy disclosure must be reviewed |
| URLhaus (abuse.ch) | Malware URL intelligence feed/query where supported | Confirm current public API/feed rules; token may be required for some endpoints | Query identifiers/URLs may be disclosed; observe service rate limits and usage terms |

Providers are candidates, not commitments. Do not put credentials in chat or source control. Store them in a secret manager/environment settings with least privilege. The app must expose which providers actually ran, their timestamps, and any failure/quota state.

## Other infrastructure (planned)

- PostgreSQL: durable scan/provider-result records and migration history.
- Redis: job queue and short-lived coordination.
- GitHub Actions: repository CI; GitHub repository access is already configured.

## Required permissions before integrations

1. The user chooses which provider(s) to enable and supplies/authorizes an API key via an approved secret-setting mechanism.
2. For Google Safe Browsing, a Google Cloud project owner must enable the API and configure key restrictions/quota/billing if applicable.
3. For VirusTotal, the API key must be permitted to use the needed endpoints within the selected plan's limits.
4. Outbound HTTPS access from an isolated worker must be allowed only to the selected provider endpoints. No broad arbitrary-target egress is needed for reputation-only provider calls.

No API key or provider access was present in the inspected project/repository. Until granted and verified, scans remain disabled.
