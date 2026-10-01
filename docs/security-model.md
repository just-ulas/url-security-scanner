# Security model (initial baseline)

## Scope

This project is intended for defensive URL/domain reputation checks only. It must not exploit targets, brute-force accounts, bypass access controls, or conduct unauthorized vulnerability testing. No target URL is fetched by the current code.

## Current controls

- Only `http` and `https` URL schemes are accepted by the validation helper.
- Embedded credentials (`user:password@host`) are rejected.
- Literal IP addresses must be globally routable; loopback, private, link-local, reserved, and otherwise non-global literals are rejected.
- The scan API returns an explicit not-implemented response after validation. No provider or detection result is generated.

These checks are input hygiene, **not** a complete SSRF boundary. Hostnames can resolve to internal addresses or change between validation and connection. Do not add target fetches until connection-time DNS/redirect validation and network egress restrictions are in place.

## Required before live scanning

- Never fetch arbitrary submitted URLs from the API process. Use provider APIs or a constrained isolated worker/egress proxy.
- Re-resolve and validate every redirect and the final peer address; deny private, loopback, link-local, multicast, reserved, and metadata-service ranges for IPv4 and IPv6.
- Apply strict connect/read timeouts, response-byte limits, content-type allowlists, redirect limits, concurrency limits, and cancellation.
- Keep API keys server-side, restrict their privileges/quotas, rotate on exposure, and do not put them in git, browser bundles, URLs, or logs.
- Treat submitted URLs as potentially secret; disclose third-party sharing, minimize stored data, redact logs, encrypt sensitive storage, and implement deletion/retention controls.
- Rate-limit scan creation, use idempotency and abuse controls, and require authentication before allowing broad or costly use.
- Preserve provider attribution and raw status; distinguish no data from a negative verdict.

## Reporting invariant

The system may say “clean” only when an identified provider explicitly supplies a clean verdict under its documented semantics. No hit, unavailable provider, timeout, quota error, unsupported URL, or partial data must never be displayed as “safe”.
