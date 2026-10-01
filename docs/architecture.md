# mimari ve geliştirme planı

## seçilen başlangıç yapısı

- **arayüz:** react, typescript ve vite. sahte tarama sonucu üretmeyen, kullanıcıya durumu açıkça anlatan bir arayüz.
- **api:** python 3.12 veya üzeri, fastapi ve pydantic settings.
- **veritabanı (ileride):** tarama kayıtları ve servis yanıtları için postgresql, sqlalchemy ve alembic.
- **iş kuyruğu (ileride):** redis ve ayrı bir arka plan işçisi. kalıcı iş takibi kurulana kadar kuyruk kapalı kalacak.
- **yerel geliştirme:** docker compose yalnızca yerel bağımlılıkları başlatmak için kullanılıyor; production kurulumu yok.
- **otomatik kontroller:** github actions, backend testlerini ve arayüz derlemesini çalıştırıyor.

## gerçek tarama açıldığında izlenecek yol

1. yalnızca `http` veya `https` bağlantılarını kabul et; adresi kontrol ederken bağlantının kendisini açma. hatalı adresleri, kullanıcı adı/parola içeren bağlantıları ve genel kullanıma açık olmayan ip adreslerini reddet.
2. isteği veritabanına kaydet ve işi kuyruğa ekle. bu bölüm henüz yazılmadı.
3. arka plan işçisi yalnızca açıkça etkinleştirilen güvenlik servislerinin belgelenmiş api'lerini çağırsın. hedefe saldırma, açık arama veya sayfaları dolaşma özelliği ekleme.
4. her servisin yanıtını ayrı sakla; hangi servisten, ne zaman ve hangi kaynakla geldiğini koru.
5. sonuçları `malicious`, `suspicious`, `clean`, `unknown` veya `error` olarak ayır. `clean` ancak servis açıkça böyle bir sonuç döndürürse kullanılabilir. servis yoksa, zaman aşımı olursa, kota dolarsa ya da yanıt okunamazsa “temiz” deme.
6. ham bağlantıyı ve servis yanıtlarını belirli bir süre sonra sil; günlüklerdeki gizli bilgileri maskele.

## dış bağlantı ve ssrf sınırı

mevcut api adres biçimini kontrol eder; alan adını çözümlemez, bağlantıyı açmaz ve tarama yapmaz. ileride dışarı istek göndermeden önce her yönlendirmede dns yanıtını ve bağlanılan ip adresini yeniden kontrol etmek, yerel/ağ içi adresleri engellemek, dns değişimini hesaba katmak ve dış trafiği kısıtlamak gerekir. mümkünse hedef siteyi açmak yerine güvenlik servislerinin kendi api'lerini kullan. yalnızca adres metnini kontrol etmek ssrf saldırılarına karşı yeterli değildir.

## sonuçlara güven ve kaynak gösterimi

gösterilen her bulgunun hangi servisten ve ne zaman geldiği belli olmalı. servisler anlaşamıyorsa bu farkı gizleme; tek bir kesinlik puanı uydurma. bir serviste sonuç bulunmaması bağlantının güvenli olduğunu kanıtlamaz. sezgisel kontroller yapılırsa bunları kesin tespit gibi değil, gerekçesiyle birlikte tahmin olarak göster.

## aşamalar

1. **başlangıç (mevcut):** depo yapısı, geliştirme notları, sağlık kontrolü, adres biçimi kontrolü ve testler. tarama yok.
2. **gerçek servisler:** kullanılacak servisleri belirle, erişim anahtarlarını yapılandır, yanıtları ve kotaları test et, veri paylaşımını kullanıcıya anlat.
3. **kalıcı işler:** veritabanı şeması, migration, kuyruk, tekrar deneme, kayıt takibi ve saklama/silme kuralları.
4. **ürünü sağlamlaştırma:** arayüz akışını tamamla, oturum açma ve kullanım sınırları ekle, izleme ve güvenlik incelemesi yap.

ilk aşamada production yayını özellikle kapsam dışı.
