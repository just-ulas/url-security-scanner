# Repository working rules

- Preserve existing behavior; review the current code before editing it.
- Never fabricate scan results, provider detections, or completed checks.
- A missing, unreachable, rate-limited, or unconfigured provider is `unknown`/`error`, not `clean`.
- Do not fetch arbitrary submitted URLs from the API process. Implement and review SSRF/network-egress defenses before any target fetch capability.
- Keep credentials out of git and browser code. Document provider attribution, data sharing, quotas, and retention.
- Run backend tests and frontend type/build checks before committing changes.
- Production deployment requires explicit scope and security/operational review; this scaffold is not production-ready.
