import './style.css';

export default function App() {
  return (
    <main className="shell">
      <header>
        <p className="eyebrow">bağlantılar hakkında daha net bilgi</p>
        <h1>bağlantı güvenlik kontrolü</h1>
        <p className="intro">
          bir bağlantı hakkında gerçek güvenlik servislerinden bilgi toplamayı
          amaçlıyoruz. şimdilik bu servislerden hiçbirine bağlı değiliz.
        </p>
      </header>
      <section className="notice" role="status">
        <strong>henüz tarama yapamıyoruz</strong>
        <p>
          bu sayfada hiçbir bağlantıyı güvenlik servisine göndermedik; elimizde
          gösterilecek bir sonuç da yok. servisleri bağladığımızda hangi servisin
          ne söylediğini ayrı ayrı göstereceğiz. bilgi gelmezse bunu da saklamadan
          belirteceğiz.
        </p>
      </section>
      <section className="roadmap">
        <h2>şu an neler hazır?</h2>
        <ul>
          <li>api ayakta mı kontrolü ve bağlantı biçimi kontrolü: hazır</li>
          <li>gerçek güvenlik servislerinden bilgi alma: henüz yok</li>
          <li>sonuçları kaydetme ve arka planda tarama: henüz yok</li>
        </ul>
      </section>
      <footer>geliştirme aşamasında · yayına alınmadı</footer>
    </main>
  );
}
