# URL Security Scanner

Defensive URL/domain reputation analysis platform scaffold. The repository currently contains **no legacy scanner implementation**: the original repository had only this project-description paragraph. No live scan provider has been integrated yet, and the application intentionally does not claim that a URL is safe or malicious.

> Current state: repository structure and development baseline are being established. Scan execution is disabled until real providers, persistence, worker processing, privacy disclosures, and operational controls are implemented and tested.

## Repository layout

```text
backend/       FastAPI API scaffold, URL input policy, provider contracts, tests
frontend/      React + TypeScript + Vite UI scaffold; no simulated scan output
docs/          Architecture, security, provider, and development notes
.github/       CI checks
.env.example   Names of optional credentials; values are never committed
compose.yaml   Local PostgreSQL and Redis development dependencies only
```

## Development prerequisites

- Python 3.12+
- Node.js 22+ and pnpm
- Docker Engine + Docker Compose plugin (only needed for local Postgres/Redis)
- Git

Start local data services with `docker compose up -d postgres redis`. The API and UI run separately during development. See [Development setup](docs/development.md).

## Current API behavior

- `GET /healthz` reports process health only; it is not a security scan.
- `POST /api/v1/scans` validates the URL syntax/policy and returns `501 Not Implemented` for otherwise valid input until a real scanning pipeline is available.
- There are no mock findings, fabricated detections, or “safe” verdicts.

## Security and privacy

See [Security model](docs/security-model.md), [Architecture](docs/architecture.md), and [External services](docs/external-services.md). User-submitted URLs may contain secrets (tokens, reset links, private paths). A future provider integration may disclose submitted URLs to that provider; explicit product disclosure, data minimization, retention controls, SSRF protections, and provider-specific attribution are required before enabling scanning.

## Status

- [x] Main GitHub repository exists and is used as the source of truth.
- [x] Baseline frontend/backend/docs/test/config structure.
- [x] Honest disabled-scan API scaffold and safe URL input checks.
- [ ] Real reputation provider integration and credentials.
- [ ] Persistent scan records, queue/worker execution, migrations, and retention policy.
- [ ] Full UI workflow, authentication/authorization, rate limits, deployment hardening, and production rollout.
