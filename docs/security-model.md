# güvenlik yaklaşımı: yerel beta

## kapsam

bu proje yalnızca bağlantı/domain güvenliğini savunma amaçlı değerlendirmek içindir. kullanıcıların girdikleri adresler, izinli http başlıkları, dns/tls gözlemi ve resmi itibar servisi yanıtlarıyla sınırlıdır. exploit, parola denemesi, port taraması, erişim kontrolü aşma, genel sayfa dolaşma veya zarar verici test yoktur.

## uygulanan korumalar

- yalnızca `http` ve `https`; kullanıcı adı/parola içeren url, localhost/şirket içi ad, genel olmayan ip, varsayılan dışı port, kontrol karakteri ve 2048 karakterden uzun url reddedilir.
- tüm dns adresleri denetlenir; sonuçlardan biri bile global değilse hedefe istek kurulmaz. bağlantıda dns yeniden sorgusu yerine kontrol edilmiş ip sabitlenir.
- otomatik yönlendirme kapalıdır. her `location` yeniden normalize edilir ve sonraki istek öncesinde dns tekrar kontrol edilip sabitlenir. en fazla beş yönlendirme izlenir; özel adrese yönlendirmede iş durur.
- tls sertifika doğrulaması açıktır. bağlantı zaman aşımı 4 saniye, toplam istek süresi 12 saniye, yanıt gövdesi en fazla 256 kib okunur ve **yanıt içeriği saklanmaz**. body analizi, script çalıştırma veya web crawl yapılmaz.
- provider çağrıları yapılandırılmış anahtar olmadan devreye girmez. provider hatası, kota, eşleşmesizlik ve eksik anahtar ayrı durum kodlarıdır; temiz bulguya çevrilmez.
- api'de redis tabanlı ip rate limit ve iş kuyruğu sınırı vardır; nginx create endpoint'ine ek yerel rate limit uygular. compose database/redis portları host'a açmaz; frontend portu loopback'e bağlanır.

## önemle bilinmesi gerekenler

dns sabitlemesi worker'a özel `aiohttp` resolver ile uygulanır. container dışındaki üretim ağı için ayrı egress firewall/allowlist yapılandırılmamıştır; worker compose ağı hâlâ genel internete çıkabilir. bu nedenle sadece localhost'ta, yetkili ve genel erişime açık hedeflerde geliştirme/test et.

taranan url (path/query dahil), ölçüm metadata'sı ve sağlayıcı yanıtları postgresql'de saklanır. otomatik süre sonu, kullanıcı bazlı silme, şifreleme-at-rest yönetimi, log redaction ve yedekleme politikası yoktur. arayüz url'nin anahtarı ayarlı provider'larla paylaşılabileceğini söyler; hassas token içeren linkleri gönderme.

## production için tamamlanması gerekenler

- kimlik doğrulama, kullanıcı/kurum izinleri, tarama geçmişine erişim denetimi ve csrf/abuse kontrolleri.
- veri saklama/silme süresi, kullanıcı silme endpoint'i, secret manager ve log redaction.
- worker egress için dns ve servis hedeflerine allowlist, ağ firewall politikası, dns rebinding saldırılarına karşı bağımsız kontrol.
- gerçek provider anahtarlarıyla kota/hata/yanıt doğrulaması, dependency scanning, threat modeling, penetration test değil savunma incelemesi.
- izleme/alarm, veritabanı yedekleme/geri yükleme ve migration rollback planı.
- production hosting/https ve güvenlik review'u.

production deployment yapılmadı ve yapılmamalı. eksik maddeler çözülmeden servisi genel ağa açma.
