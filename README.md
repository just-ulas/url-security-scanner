# bağlantı güvenlik kontrolü

bir bağlantı şüpheli göründüğünde, tahmin yerine kaynak gösteren kontroller görmek istiyoruz. bu proje; gerçek itibar servislerini, url'nin dns/https/http yanıtını ve servise ait ölçüm zamanını tek yerde gösteren savunma amaçlı bir web uygulamasıdır.

**bu sürüm geliştirme betasıdır; production'a yayımlanmadı.** uygulama gerçek api ve worker akışını, veritabanı kayıtlarını ve url sorgulama adapter'larını içeriyor. ancak erişim anahtarları sağlanmadığı için virustotal, google safe browsing ve urlhaus şu anda ağa istek göndermiyor. anahtarı olmayan servis “bağlı değil”, eşleşme bulamayan servis “bilinmiyor” görünür; sahte tespit veya uydurma sonuç yoktur.

## proje yapısı

```text
backend/
  app/api/          tarama api şemaları
  app/core/         ayarlar ve redis bağımlılığı
  app/providers/    virustotal, google safe browsing ve urlhaus adapter'ları
  app/services/     url politikası, tarama kuyruğu ve güvenli metadata isteği
  app/worker/       redis/rq arka plan işçisi
  migrations/       alembic veritabanı sürümleri
  tests/            api, adapter, worker, veri modeli ve ssrf testleri
frontend/
  src/              react/typescript arayüzü
  nginx.conf        api proxy ve istek sınırları
compose.yaml        yerel beta: arayüz, api, postgresql, redis, worker
.github/workflows/ci.yml
.env.example       gizli olmayan yerel ayar örneği
```

## yerel geliştirme

python 3.12+, node.js 22+, pnpm ve docker compose gerekir. ayrıntılar ve docker dışı geliştirme yolu için [geliştirme notlarına](docs/development.md) bak.

```bash
cp .env.example .env
docker compose up -d --build
```

arayüz `http://127.0.0.1:5173` adresinde açılır. bu yalnızca yerel geliştirme ortamıdır. uygulama portları genel ağa açılmamıştır. api belgeleri `http://127.0.0.1:5173/docs` adresindedir.

## gerçek tarama nasıl çalışıyor?

- `post /api/scans` bağlantıyı doğrular, tarama kaydı açar ve işi redis/rq kuyruğuna ekler.
- worker public dns yanıtını kontrol eder, yalnızca doğruladığı ip'lere bağlanır ve her yönlendirmede yeniden kontrol yapar. yerel/ağ içi ip'ler, kimlik bilgisi içeren url'ler ve varsayılan olmayan portlar engellenir.
- hedefe en fazla beş yönlendirme izlenir; zaman aşımı ve okunabilecek yanıt verisi sınırlandırılır. yanıt gövdesi saklanmaz. bu, tam içerik ya da zararlı yazılım analizi yaptığı anlamına gelmez.
- ayarlı virustotal, google safe browsing ve urlhaus adapter'ları yalnızca ilgili sağlayıcının gerçek yanıtını kaydeder.
- `get /api/scans/{id}` tarama durumunu, `get /api/scans/{id}/results` kaynak sonuçlarını verir.

sağlayıcı eşleşmesi olmaması “güvenli” demek değildir. her motor sonucu ayrı gösterilir; genel özet yalnızca eldeki gerçek sonuçlardan hesaplanır. servisler, kaynak alanları ve yorumlama sınırları [resmi api notlarında](docs/provider-api-notes.md) yazılıdır.

## erişim ve sınırlamalar

- isteğe bağlı servis anahtarları yalnızca `.env` veya güvenli sunucu ortam değişkenlerinde tutulur; sohbete veya kaynak koda eklenmez. [dış servis ve erişim notlarına](docs/external-services.md) bak.
- taranan url veritabanına yazılır; url içindeki sorgu parametreleri gizli bilgi içerebilir ve anahtarı ayarlı servislere gönderilebilir.
- şu an oturum açma, kullanıcı bazlı yetkilendirme, otomatik veri silme ve production secret yönetimi yok. yerel geliştirme dışında çalıştırma veya genel internete açma.
- asn ve alan adı kayıt bilgisi sağlayıcısı bağlı değildir. teknoloji bilgisi yalnızca sunucunun yanıt başlıklarından alınan ipucudur.
- tehdit arama, port tarama, exploit, sayfa dolaşma veya hedefe zarar verecek işlem bu projenin kapsamında değildir.

## testler

```bash
.venv/bin/python -m pytest -q backend/tests
.venv/bin/ruff check backend
cd frontend && pnpm install --frozen-lockfile && pnpm typecheck && pnpm build
```

## durum

- api, postgresql şeması ve alembic migration'ı hazır.
- redis kuyruğu, worker ve gerçek sağlayıcı adapter'ları hazır.
- url girdisi, dns yanıtı ve yönlendirmelerde ssrf engelleri hazır.
- yerel arayüz, api proxy, testler ve ci hazır.
- hiçbir api anahtarı ayarlı değil; canlı itibar servisi yanıtı henüz doğrulanmadı.
- kimlik doğrulama, veri saklama/silme, üretim gözlemi ve güvenlik incelemesi tamamlanmadı.
