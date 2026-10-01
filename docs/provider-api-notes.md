# doğrulanmış sağlayıcı api notları

bu notlar adapter davranışının dayandığı resmi belgeleri ve sonuçların nasıl yorumlandığını kaydeder. burada anlatılanlar canlı servis yanıtı değildir.

## virustotal api v3

resmi kaynaklar: [url report](https://docs.virustotal.com/reference/url-info), [url identifier](https://docs.virustotal.com/reference/url), [url object fields](https://docs.virustotal.com/reference/url-object).

url raporu `get /api/v3/urls/{id}` ile okunur. id olarak url'nin padding'i çıkarılmış url-safe base64 biçimi kullanılabilir; erişim anahtarı `x-apikey` başlığıyla gönderilir. `last_analysis_stats` alanındaki `malicious`, `suspicious`, `harmless`, `undetected` ve `timeout` adetleri kaynak yanıtından aynen saklanır. malicious veya suspicious sonucu varsa öne alınır. ancak `harmless` sayısı sıfırdan büyük ve zararlı/şüpheli motor sayısı sıfırsa sağlayıcının “harmless” sonucu clean olarak gösterilebilir. yalnızca undetected ya da rapor bulunmaması bilinmiyor demektir.

## google safe browsing lookup api v4

resmi kaynak: [lookup api](https://developers.google.com/safe-browsing/v4/lookup-api). istek `post /v4/threatMatches:find?key=...` adresine gönderilir ve url `threatInfo.threatEntries` içinde yer alır. resmi belge, boş `matches` nesnesinin sorgulanan listelerde eşleşme olmadığını belirttiğini söylüyor. bu uygulama bunu `no_data` ve `unknown` olarak saklar; “güvenli” diye yorumlamaz. gerçek bir eşleşme, yanıtın threat type/platform/type alanlarıyla birlikte saklanır.

## urlhaus community api

resmi kaynak: [community api](https://urlhaus.abuse.ch/api/). sorgu için ücretsiz bir `auth-key` gerekiyor. yalnızca okuma amaçlı `post https://urlhaus-api.abuse.ch/v1/url/` adapter'ı kullanılır; zararlı url gönderimi veya raporlama özelliği yoktur. `query_status: no_results` “temiz” anlamına çevrilmez. kayıt bulunursa servisin `url_status`, tehdit, etiket ve tarih alanları saklanır.

## gizlilik ve kota

gerçek anahtarlar environment variables üzerinden okunur ve yanıtlara/loglara eklenmez. bu servislere taranacak url gönderilir; url sorgu parametrelerinde gizli token içeriyorsa o token da paylaşılabilir. bu nedenle arayüz taramadan önce paylaşım ve kayıt uyarısı gösterir. anahtarlar boşsa adapter'lar `not_configured` sonucu döndürür ve ağ isteği yapmaz.
