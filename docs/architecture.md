# Architecture and implementation plan

## Selected baseline

- **Frontend:** React, TypeScript, Vite. Lightweight operator-facing UI; no scan results are fabricated client-side.
- **API:** Python 3.12+, FastAPI, Pydantic Settings.
- **Persistence (planned):** PostgreSQL with SQLAlchemy + Alembic; scan records and provider-specific observations.
- **Queue (planned):** Redis with a separately deployed worker. Queueing remains disabled until a durable job lifecycle is implemented.
- **Local orchestration:** Docker Compose for development dependencies only; no production deployment is included.
- **CI:** GitHub Actions for backend tests and frontend build/type checks.

## Intended request lifecycle

1. Accept an HTTP(S) URL, canonicalize it without fetching it, and reject malformed inputs, userinfo, and non-public IP literals.
2. Create a scan record and enqueue a job (not implemented yet).
3. A worker invokes explicitly enabled reputation providers using each provider's documented API; it does not exploit, probe, or crawl targets.
4. Store each provider result separately with provider name, observation time, provider reference, and an evidence/verdict status.
5. Return a summary that distinguishes `malicious`, `suspicious`, `clean`, `unknown`, and `error`; `clean` is permitted only when a provider actually returns a clean verdict. Provider absence, timeout, quota exhaustion, or parsing errors must remain `unknown`/`error`, never a clean verdict.
6. Expire raw URLs and provider payloads under a documented retention policy; redact secrets in logs.

## SSRF and egress boundary

The current API validates syntax and rejects literal non-global IP addresses but **does not resolve hostnames, fetch submitted URLs, or perform a scan**. Before any outbound fetch is added, implement DNS resolution and revalidation at connection time, redirect-by-redirect checks, private/link-local/loopback/reserved IPv4 and IPv6 denial, strict egress controls, response size/time limits, and DNS-rebinding defenses. Prefer provider APIs that accept a URL/hash over visiting the target directly. A firewall or dedicated egress proxy is required; application-level parsing alone is not a complete SSRF defense.

## Trust and attribution

Every future observation must retain the provider and timestamp. Conflicting provider results must be shown as disagreement rather than collapsed into an invented certainty score. Lack of a provider hit is not proof of safety. Heuristic findings must be labeled as heuristics and explain their evidence.

## Phases

1. **Foundation (current):** repo structure, dev docs, health endpoint, URL syntax policy, tests, no scan execution.
2. **Provider integration:** choose providers, obtain keys, implement response parsing/quotas/timeouts, contract tests, and user-facing data disclosure.
3. **Durable pipeline:** schema/migrations, queue, idempotency, retries, audit/retention, and worker observability.
4. **Product hardening:** UI, authentication, abuse controls, operational monitoring, security review, and deployment readiness.

Production deployment is explicitly out of scope for the initial stage.
