# geliştirme ortamını hazırlama

## gerekenler

python 3.12 veya üzeri, node.js 22 veya üzeri, pnpm ve git gerekiyor. yerel postgresql ile redis'i çalıştırmak istersen docker engine ve docker compose da gerekli.

## yerel kurulum

```bash
cp .env.example .env
# bu servisler yalnızca yerel geliştirme içindir; yayına alma işlemi değildir.
docker compose up -d postgres redis

python3 -m venv .venv
. .venv/bin/activate
pip install -e 'backend[dev]'
uvicorn app.main:app --app-dir backend --reload --port 8000
```

arayüzü ikinci bir terminalde başlat:

```bash
cd frontend
pnpm install
pnpm dev --host 127.0.0.1
```

arayüz `http://127.0.0.1:5173`, api sağlık kontrolü ise `http://127.0.0.1:8000/healthz` adresinde açılır. şu an veritabanı henüz kullanılmıyor; migration, redis kuyruğu ve gerçek tarama da devreye alınmadı. compose dosyası yalnızca geliştirme servislerini başlatır, production kurulumu yapmaz.

## kontroller

```bash
cd /path/to/url-security-scanner
. .venv/bin/activate
pytest
ruff check backend
cd frontend && pnpm typecheck && pnpm build
```

`.env` dosyasını veya servis anahtarlarını git'e ekleme. gönderilen adreslerin hangi servislerle paylaşılacağı, kullanım sınırları ve gerçek sonuçların nasıl gösterileceği netleşmeden taramayı açma.
