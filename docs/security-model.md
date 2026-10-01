# güvenlik yaklaşımı: mevcut başlangıç

## kapsam

bu proje yalnızca bağlantılar hakkında savunma amaçlı itibar bilgisi toplamak için tasarlanıyor. hedeflere açık arama, parola deneme, erişim kontrollerini aşma veya izinsiz güvenlik testi yapılmayacak. şu anki kod gönderilen bağlantıyı açmıyor.

## şu anki kontroller

- yalnızca `http` ve `https` adres biçimleri kabul ediliyor.
- adresin içine yazılmış kullanıcı adı veya parola reddediliyor.
- doğrudan yazılmış, genel internete açık olmayan ip adresleri reddediliyor.
- api, biçim kontrolünden sonra da tarama başlatmıyor; herhangi bir güvenlik servisi çağrılmıyor ve bulgu üretilmiyor.

bunlar yalnızca ilk giriş kontrolleri; ssrf'ye karşı tam koruma değiller. bir alan adı şirket içi ya da yerel bir ip adresine çözülebilir veya sonradan başka bir adrese yönlenebilir. bağlantı anında dns ve hedef ip kontrolüyle dış trafik kısıtları hazır olmadan hedef adreslere istek ekleme.

## gerçek taramadan önce yapılması gerekenler

- api sürecinden rastgele bağlantı açma. güvenlik servislerinin api'lerini kullan veya dış trafiği çok sıkı sınırlandırılmış ayrı bir işçi çalıştır.
- her yönlendirmede ve son bağlantı noktasında ip adresini yeniden kontrol et. yerel, özel ağ, bağlantı-yerel, çoklu yayın ve bulut metadata adreslerini engelle.
- bağlantı ve yanıt süresini, indirilecek veri miktarını, yönlendirme sayısını ve eşzamanlı işleri sınırla.
- erişim anahtarlarını yalnızca sunucu tarafında tut; git'e, arayüze, adres çubuğuna veya günlük kayıtlarına koyma.
- gönderilen bağlantıların gizli bilgi içerebileceğini varsay. dış servislerle paylaşımı açıkla, gereken en az veriyi sakla ve silme süresini belirle.
- kullanım sınırı ve kötüye kullanım önlemleri ekle; geniş kullanıma açmadan önce oturum açmayı zorunlu kıl.
- her sonucu hangi servisin verdiğiyle birlikte göster; “sonuç yok” ile “tehlike yok” ifadelerini birbirine karıştırma.

## sonuçları gösterme kuralı

yalnızca adı belli bir servis açıkça temiz sonucu döndürürse bu sonuç temiz olarak gösterilebilir. eşleşme bulunmaması, servise ulaşılamaması, kota veya zaman aşımı sorunu, desteklenmeyen adres ya da eksik yanıt “güvenli” anlamına gelmez.
