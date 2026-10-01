# dış servisler ve gereken erişimler

üç gerçek itibar servisi için adapter kodu hazır. **bu oturumda herhangi bir gerçek servis anahtarı yok; adapter'lar `not_configured` döndürüyor ve bu servislere istek atmıyor.** canlı endpoint doğrulaması yapılmış sayılmaz. anahtarları bu depoya, sohbete veya arayüze koyma; sunucu tarafındaki `.env` ya da ileride kurulacak secret manager üzerinden sağlamalısın.

| servis | hangi yanıt kullanılır? | gereken izin/ayar |
|---|---|---|
| virustotal api v3 | mevcut url raporundaki engine sayıları ve analiz tarihi | virustotal hesabı ve url report uç noktasını çağırabilen api key; hesap/kota bu erişimi vermeli |
| google safe browsing lookup v4 | bilinen tehdit listelerinde url eşleşmesi | google cloud projesinde safe browsing api etkinleştirmesi ve bu api için geçerli api key; anahtarın restriction ve kota ayarı doğru olmalı |
| urlhaus community api | mevcut urlhaus kaydı, durum, etiket ve kayıt tarihi | abuse.ch community api key (`auth-key`) ve query endpoint erişimi |

anahtar veya sağlayıcı yanıtı olmadığı için bu proje şu anda canlı itibar tespiti yapmıyor. gerçek bir servis anahtarı olmadan yalnızca yerel tarama akışının, url politikalarının ve sağlayıcı yok durumunun testleri yapıldı. her adapter'ın gerçek key ile denemesi öncesinde ilgili servisin güncel kotalarını ve kullanım şartlarını doğrula.

## tarama verisinin paylaşımı

provider lookup'ı url'yi ilgili servise gönderir. url'nin path/query bölümü parola sıfırlama kodu, erişim token'ı veya kişisel veri içeriyorsa bu bilgi servise gidebilir. uygulama taramayı veritabanına kaydeder. mevcut geliştirme sürümünde otomatik saklama/silme süresi belirlenmemiştir. hassas/kişiye özel bağlantıları tarama.

google api key lookup isteğinde query parametresi olarak gönderilir. bu kod api anahtarını kullanıcıya dönen yanıta koymaz; yine de production proxy, tracing ve hata günlüklerinin query string'i kaydetmesini engelle.

## metadata için dış ağ

hedefe doğrudan http isteği yalnızca worker tarafından, dns/ip/redirect denetimiyle yapılır. provider api'leri, veritabanı ve redis dışındaki egress bir ağ/firewall allowlist'i ile henüz sınırlandırılmış değildir. asn ve domain registration sorgusu için ek servis bağlanmamıştır; arayüz bunu açıkça “bağlı değil” gösterir.

## gerekli dış izinler

anahtarları etkinleştirmeden önce hesap/organization yöneticisinin ilgili resmi servis panelinden key oluşturması gerekir. güvenlik gereği anahtarı bu sohbete gönderme. geçerli bir sunucu secret alanı/connector henüz bağlı değildir; ilk local test için `.env` dosyasına kendin güvenli biçimde ekleyebilir veya ileride hosting ortamında secret olarak tanımlayabilirsin. production deployment bu aşamada yapılmadı.
