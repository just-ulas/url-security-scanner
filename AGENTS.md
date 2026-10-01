# bu depoda çalışırken

- önce ilgili kodu oku; çalışan davranışı anlamadan değiştirme.
- tarama sonucu, servis tespiti ya da yapılmamış kontrolü olmuş gibi gösterme.
- erişilemeyen, kota sınırına takılan veya bağlı olmayan servis için sonucu “bilinmiyor” ya da “hata” olarak bırak; temiz deme.
- api sürecinden gönderilen rastgele bağlantıları açma. hedefe istek eklemeden önce ssrf ve dış trafik korumalarını tamamla.
- erişim anahtarlarını git'e veya tarayıcı koduna koyma. servis kaynağını, veri paylaşımını, kotaları ve saklama süresini belgeye ekle.
- commit atmadan önce backend testlerini ve arayüz tür/derleme kontrollerini çalıştır.
- production yayını için ayrıca kapsam belirlemesi ve güvenlik/işletim incelemesi gerekir; bu iskelet henüz yayına hazır değil.
