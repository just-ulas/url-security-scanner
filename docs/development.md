# Development setup

## Requirements

Python 3.12+, Node.js 22+, pnpm, Git. Docker Engine and the Compose plugin are needed only for local PostgreSQL/Redis.

## Local setup

```bash
cp .env.example .env
# Start only local development dependencies; not a production deployment.
docker compose up -d postgres redis

python3 -m venv .venv
. .venv/bin/activate
pip install -e 'backend[dev]'
uvicorn app.main:app --app-dir backend --reload --port 8000
```

In a second terminal:

```bash
cd frontend
pnpm install
pnpm dev --host 127.0.0.1
```

The UI is served at `http://127.0.0.1:5173`; API health at `http://127.0.0.1:8000/healthz`. At this baseline no migrations, DB usage, Redis queue, or actual scan execution are enabled. Docker Compose only starts local PostgreSQL and Redis; it is not a production deployment.

## Checks

```bash
cd /path/to/url-security-scanner
. .venv/bin/activate
pytest
ruff check backend
cd frontend && pnpm typecheck && pnpm build
```

Do not commit `.env` or provider credentials. Do not enable provider integrations until their data-sharing disclosure, quota limits, and live-result attribution are implemented.
