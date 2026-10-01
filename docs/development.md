# geliştirme ortamını hazırlama

## gerekenler

- docker engine ve docker compose v2 — tam yerel yığın için
- python 3.12 veya üzeri, node.js 22 ve pnpm 9.15.4 — kod ve testler için
- postgresql 16 ve redis 7 — docker dışı native geliştirme için

dependency sürümleri ve başlangıç yapılandırmaları depoda bulunur. gerçek servis anahtarları bu depoda tutulmaz.

## tam yığını başlatma

repository kökünde:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

arayüz `http://127.0.0.1:5173`, api belgeleri `http://127.0.0.1:5173/docs`, readiness `http://127.0.0.1:5173/api/health` adresinde. yalnızca arayüz portu yerel host'a bağlanır; postgresql, redis, api ve worker portları dışarı açılmaz. veritabanı migration'ı api başlarken çalışır. `.env` içindeki virustotal, google safe browsing ve urlhaus anahtarları boşsa ilgili provider'lar `not_configured` döner ve hiçbir provider ağına istek göndermez.

`docker compose logs -f api worker` ile yerel logları izleyebilir; `docker compose down` ile servisleri durdurabilirsin. `docker compose down -v` kalıcı geliştirme verilerini de siler; bunu özellikle istemeden çalıştırma.

## docker olmadan api ve arayüz

postgresql/redis servisleri çalışıyor olmalı, `.env` içindeki `database_url` ile `redis_url` yerel servislere bakmalı. repository kökünde:

```bash
python3 -m venv .venv
.venv/bin/pip install -e 'backend[dev]'
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

ikinci süreçte işçiyi başlat:

```bash
cd backend
../.venv/bin/python -m app.worker.runner
```

üçüncü süreçte arayüzü başlat:

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev --host 127.0.0.1
```

native api `http://127.0.0.1:8000`, arayüz `http://127.0.0.1:5173` adresindedir. `frontend/vite.config.ts`, `/api`, `/docs` ve `/openapi.json` isteklerini api'ye aktarır.

## doğrulama

```bash
.venv/bin/python -m pytest -q backend/tests
.venv/bin/ruff check backend
cd frontend
pnpm install --frozen-lockfile
pnpm typecheck
pnpm build
```

testler mock provider yanıtları kullanır; gerçek servis çağrısı veya bulgu üretmez. production kurulumu, genel internete açma veya kullanıcıların tarayabileceği bir servis başlatma bu geliştirme adımlarının parçası değildir.
