# dış servisler ve gereken erişimler

şu an projede hiçbir bağlantı itibarı servisi bağlı değil ve bu servislerden hiçbirine istek gönderilmiyor.

## ileride değerlendirilebilecek servisler

| servis | ne için kullanılabilir? | gereken erişim | gizlilik notu |
|---|---|---|---|
| virustotal api v3 | bağlantı ve alan adı itibarı, kaynak gösterilen servis sonuçları | gerekli uç noktalara izin veren bir api anahtarı ve uygun kota | gönderilen bağlantı ya da kimlik bilgisi virustotal ile paylaşılır; kullanım koşulları ve paylaşım biçimi önceden incelenmeli |
| google safe browsing | bilinen zararlı bağlantıları sorgulama | google cloud projesi, etkin api, api anahtarı ve gerekiyorsa kota/faturalandırma ayarı | sorgulanan bağlantı google'a gider; koşullar ve gizlilik açıklaması kontrol edilmeli |
| urlhaus (abuse.ch) | zararlı yazılım bağlantısı bilgisi veya akışları | kullanılacak uç noktanın güncel koşulları; bazı işlemlerde erişim anahtarı gerekebilir | sorgu bilgisi paylaşılabilir; servis sınırlarına uyulmalı |

bunlar şu an bağlı servisler değil, yalnızca değerlendirilecek seçenekler. erişim anahtarlarını sohbete veya kaynak koduna yazma. ileride her sonuçta hangi servisin çalıştığı, ne zaman yanıt verdiği ve hata/kota durumu gösterilmeli.

## ileride gereken altyapı

- postgresql: tarama ve servis yanıtı kayıtları.
- redis: arka plan işleri için kuyruk.
- github actions: kaynak kod kontrolleri; depo erişimi zaten yapılandırılmış.

## servisleri bağlamak için gereken izinler

1. önce hangi servislerin kullanılacağına karar verilmeli; anahtarlar güvenli bir ayar alanına eklenmeli.
2. google safe browsing seçilirse google cloud projesinin sahibi api'yi açmalı ve anahtar ile kota ayarlarını yapmalı.
3. virustotal seçilirse kullanılan hesap ve anahtar, gerekli sorguları plan sınırları içinde yapabilmeli.
4. ayrı işçinin yalnızca seçilen servislerin https adreslerine çıkmasına izin verilmeli. itibar sorgusu için rastgele hedeflere bağlantı açmaya gerek yok.

inceleme sırasında depoda servis anahtarı veya dış servis erişimi bulunmadı. gerçek bir servis bağlanıp doğrulanana kadar tarama kapalı kalacak.
