# bağlantı güvenlik kontrolü

bazen bir bağlantıya tıklamadan önce “acaba güvenli mi?” diye düşünüyoruz. bu proje, bir bağlantı hakkında gerçek güvenlik servislerinden bilgi toplamayı amaçlıyor. ama şu an elimizde çalışan eski bir tarayıcı yoktu; depoda yalnızca kısa bir fikir açıklaması vardı. eklediğimiz yapı, projeyi buradan geliştirebilmek için hazırlanmış bir başlangıç iskeleti.

**şu an hiçbir güvenlik servisine bağlanmıyoruz, gönderilen adresleri açmıyoruz ve tarama sonucu üretmiyoruz.** bu yüzden sayfa bir bağlantıyı güvenli ya da tehlikeli diye etiketlemiyor.

## projede neler var?

```text
backend/       api başlangıç kodu, adres biçim kontrolü ve testler
frontend/      react ve typescript ile hazırlanmış arayüz
backend/app/worker/  ileride kullanılacak işçi görevlerinin yeri
docs/          mimari, güvenlik, geliştirme ve servis notları
.github/       otomatik test ve derleme iş akışı
.env.example   yerel ayar örneği; gerçek anahtar içermez
compose.yaml   yerel geliştirme için postgresql ve redis
```

## geliştirmek için gerekenler

- python 3.12 veya üzeri
- node.js 22 veya üzeri ve pnpm
- git
- yalnızca yerel postgresql ve redis çalıştırmak için docker engine ile docker compose

kurulum adımları için [geliştirme notlarına](docs/development.md) bak. bu yapı yerel geliştirme içindir; production ortamına kurulmuş değildir.

## şu an nasıl çalışıyor?

- `get /healthz` yalnızca api sürecinin ayakta olup olmadığını söyler; bir bağlantıyı taramaz.
- `post /api/v1/scans` adresin biçimini kontrol eder. adres uygunsa bile tarama yapmaz ve `501` döndürür.
- sahte bulgu, uydurma tespit ya da “güvenli” sonucu gösterilmez.

## güvenlik ve gizlilik

bir bağlantının içinde parola sıfırlama kodu ya da kişiye özel başka bilgiler bulunabilir. ileride gerçek servisleri bağlarsak, gönderdiğin adres bu servislerle paylaşılabilir. taramayı açmadan önce bunu açıkça anlatmamız; hangi veriyi sakladığımızı, ne zaman sildiğimizi ve dış bağlantıları nasıl kısıtladığımızı belirlememiz gerekiyor. daha fazlası için [güvenlik notlarını](docs/security-model.md), [mimari planı](docs/architecture.md) ve [dış servisler listesini](docs/external-services.md) inceleyebilirsin.

## proje durumu

- [x] github deposu ve temel proje yapısı hazır.
- [x] arayüz, api başlangıcı, testler ve geliştirme notları eklendi.
- [x] adres biçimi kontrol ediliyor; api henüz tarama yapmadığını açıkça söylüyor.
- [ ] gerçek güvenlik servislerine bağlanma ve gerekli erişim anahtarları.
- [ ] tarama kayıtlarını saklama, veritabanı değişiklikleri ve arka plan işçisi.
- [ ] oturum açma, kullanım sınırları, veri saklama/silme kuralları ve yayına hazırlık.
