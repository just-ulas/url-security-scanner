# mimari ve geliştirme planı

## mevcut bileşenler

- **arayüz:** react + typescript + vite. same-origin api istekleri nginx üzerinden api'ye gider; tarama durumunu sorgular ve gerçek kayıtlı veriyi gösterir.
- **api:** fastapi. url doğrulama, ip bazlı basit rate limit, aynı url için aktif tarama birleştirme, tarama kaydı ve redis kuyruğu yönetimi.
- **veritabanı:** postgresql 16. `targets`, `scans`, `scan_metadata` ve `provider_results` tabloları sqlalchemy modelleriyle tanımlı; alembic migration ile kurulur.
- **iş kuyruğu:** redis 7 + rq. api işi kuyruğa ekler; bağımsız worker metadata kontrolünü ve itibar provider'larını çalıştırır.
- **itibar servisleri:** virustotal v3, google safe browsing lookup v4 ve urlhaus community api adapter'ları. anahtarlar ayarlı değilse ağ çağrısı yapılmaz.
- **hedef metadata:** yalnızca worker dış ağa çıkar. dns sonuçlarının tümü public değilse istek durur, doğrulanan adresler dns sabitlemesiyle kullanılır, her yönlendirme baştan denetlenir. tls varsayılan sertifika doğrulamasıyla kurulur; http başlıkları, sınırlı yanıt metadata'sı ve tls sertifika özeti saklanır; yanıt gövdesi saklanmaz.
- **yerel runtime:** docker compose api ve frontend portlarını localhost'a bağlar; database ve redis portları host'a açılmaz. api yalnızca iç ağa, worker iç ağ ve dış ağ bağlantısına sahiptir.
- **kalite:** github actions backend testleri ile frontend tip kontrolü ve build'i çalıştırır.

## tarama akışı

1. `post /api/scans` en fazla 2048 karakterlik `http`/`https` adresi kabul eder. kullanıcı bilgileri, yerel adlar, genel olmayan ip adresleri ve varsayılan dışı portlar reddedilir; fragment atılır.
2. kanonik url/hash veritabanına yazılır. aynı hedefin devam eden işi varsa ikinci job yerine mevcut kayıt döner.
3. redis kuyruğuna `process_scan` işi yazılır. ayarlanmış bir worker alana adı çözümler; listedeki tek bir ip bile özel/ayrılmışsa bağlantı kurmaz. public adresler sabitlenmiş resolver ile istek için kullanılır.
4. işçi `http` yanıtını yönlendirme izni olmadan alır; her `location` yeni url ve dns olarak tekrar doğrulanır. maksimum beş yönlendirme; 4 saniye bağlantı, 12 saniye toplam zaman aşımı ve en fazla 256 kib yanıt örneği vardır.
5. güvenli metadata kaydedilir. yalnızca anahtarı bulunan provider'lar url itibar sorgular. her sonuç kendi durum, verdict, zaman ve sağlayıcı verileriyle ayrı tutulur.
6. tarama durumu `queued`, `running`, `completed` veya `failed`; sağlayıcı durumu `not_configured`, `no_data`, `rate_limited`, `unauthorized`, `timeout`, `unavailable`, `error` veya `completed` olabilir.

## verdict kuralları

- urlhaus ve google eşleşme yok yanıtı `unknown` verir; temiz olarak yorumlanmaz.
- virustotal motor sayıları gerçek yanıt alanlarından gösterilir. malicious/suspicious motor sayısı varsa buna öncelik verilir; yalnızca harmless sayısı varsa o provider `clean` verir.
- bir hata veya servis anahtarı eksikliği bulgu değildir ve `clean` sayılmaz.
- genel verdict yalnızca `completed` provider yanıtlarından türetilir; malicious, sonra suspicious, sonra varsa provider clean, aksi durumda unknown. arayüz her zaman provider sonuçlarını ayrı gösterir; “hiçbir listede bulunamadı” güvenlik garantisi değildir.

## güven sınırı ve production eksiği

bu kurulum production servisi değildir. kullanıcı hesabı/kimlik doğrulama yoktur; ip başına rate limit tek başına gerçek abuse kontrolü sayılmaz. taramalar için saklama/silme süresi veya kullanıcı silme akışı yoktur. url ve sağlayıcı yanıtları veritabanında kalır. worker internet çıkışı sağlayıcı hedefleriyle firewall seviyesinde sınırlandırılmadı. gerçekte alan adı/asn hizmeti, gözlemleme, yedekleme, secrets vault, migration deploy süreci ve bağımsız güvenlik denetimi yoktur. genel ağa açmadan önce bunları ele al.

## aşamalar

1. **yerel beta:** uygulama bileşenleri, adapter'lar, ssrf kontrolleri ve testler hazır; provider anahtarları verilmemiş ve production deploy yapılmamış durumda.
2. **servis bağlantısı:** anahtarları sunucu ortamında güvenli biçimde sağla; belgelenmiş kotalara ve gizlilik koşullarına göre her servisi gerçek yanıtla doğrula.
3. **ürün güvenliği:** kullanıcı kimliği/izinler, saklama ve silme, kota ve abuse kontrolü, dış egress allowlist, secret yönetimi, log redaction, izleme ve yedekleme.
4. **yayın:** yalnızca ayrı onaylı hedef ortam, risk/gizlilik incelemesi ve operasyon testlerinden sonra. ilk aşamada production yayını kapsam dışıdır.
