import { FormEvent, useEffect, useState } from 'react';
import './style.css';

type ProviderResult = {
  provider: string;
  status: string;
  verdict: string;
  observed_at: string;
  details: Record<string, unknown>;
  error_code?: string | null;
  error_message?: string | null;
};

type Scan = {
  id: string;
  url: string;
  status: string;
  overall_verdict: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  metadata?: Record<string, any> | null;
  providers: ProviderResult[];
  deduplicated: boolean;
};

const statusText: Record<string, string> = {
  queued: 'kuyrukta',
  running: 'kontrol ediliyor',
  completed: 'tamamlandı',
  failed: 'tamamlanamadı',
  not_configured: 'bağlı değil',
  no_data: 'eşleşme yok',
  rate_limited: 'kullanım sınırına ulaşıldı',
  unauthorized: 'erişim reddedildi',
  timeout: 'zamanında yanıt vermedi',
  unavailable: 'şu an ulaşılamıyor',
  error: 'hata',
  malicious: 'zararlı',
  suspicious: 'şüpheli',
  clean: 'servis temiz olarak işaretledi',
  unknown: 'bilinmiyor',
};

const providerNames: Record<string, string> = {
  virustotal: 'virustotal',
  google_safe_browsing: 'google safe browsing',
  urlhaus: 'urlhaus',
};

function label(value?: string | null): string {
  if (!value) return 'bilinmiyor';
  return statusText[value] ?? value.toLowerCase().replaceAll('_', ' ');
}

function providerSummary(result: ProviderResult): string {
  if (result.status === 'not_configured') return 'bu servisin erişim anahtarı ayarlanmamış.';
  if (result.status === 'no_data') return 'eşleşme bulunmadı; bu, bağlantının güvenli olduğunu kanıtlamaz.';
  if (result.error_message) return result.error_message;
  if (result.verdict === 'malicious') return 'servis bu adresi zararlı olarak işaretledi.';
  if (result.verdict === 'suspicious') return 'servis bu adresi şüpheli olarak işaretledi.';
  if (result.verdict === 'clean') return 'servis bu adresi kendi ölçütlerine göre temiz olarak işaretledi.';
  return 'bu servisten kesin bir güvenlik sonucu alınamadı.';
}

function MetadataPanel({ metadata }: { metadata?: Record<string, any> | null }) {
  if (!metadata) return <p className="muted">tarama bilgileri henüz oluşmadı.</p>;
  const http = metadata.http ?? {};
  const tls = metadata.tls ?? {};
  const dns = metadata.dns ?? {};
  const securityHeaders = http.security_headers ?? {};
  const dnsAddresses: string[] = metadata.resolved_ips ?? [];
  const redirects: Array<Record<string, any>> = metadata.redirect_chain ?? [];
  const technologies: Array<Record<string, any>> = metadata.detected_technologies?.items ?? [];

  return (
    <div className="metadata-grid">
      <div className="data-card">
        <span className="data-label">adres</span>
        <strong>{metadata.status === 'observed' ? 'yanıt alındı' : label(metadata.status)}</strong>
        <p>{http.final_url ?? metadata.reason ?? 'yanıt bilgisi alınamadı.'}</p>
      </div>
      <div className="data-card">
        <span className="data-label">http durumu</span>
        <strong>{http.status ?? 'bilinmiyor'}</strong>
        <p>yanıt gövdesi kaydedilmedi; en fazla 256 kb okunabilir.</p>
      </div>
      <div className="data-card wide">
        <span className="data-label">dns ve çözümlenen ip adresleri</span>
        <strong>{dnsAddresses.length ? dnsAddresses.join(', ') : label(dns.status)}</strong>
        {dns.hops?.length > 1 && <p>her yönlendirme adımı için dns yeniden kontrol edildi.</p>}
      </div>
      <div className="data-card">
        <span className="data-label">tls sertifikası</span>
        <strong>{label(tls.status)}</strong>
        {tls.issuer && <p>veren: {tls.issuer}</p>}
        {tls.not_after && <p>son geçerlilik: {tls.not_after}</p>}
      </div>
      <div className="data-card">
        <span className="data-label">alan adı / asn</span>
        <strong>{label(metadata.domain?.status)} / {label(metadata.asn?.status)}</strong>
        <p>bu bilgiler için ek bir veri servisi henüz bağlı değil.</p>
      </div>
      <div className="data-card wide">
        <span className="data-label">güvenlik başlıkları</span>
        <div className="header-list">
          {Object.entries(securityHeaders).map(([name, value]) => (
            <div key={name}><code>{name}</code><span>{value ? String(value) : 'yanıtta yok'}</span></div>
          ))}
          {!Object.keys(securityHeaders).length && <span>henüz ölçüm yok.</span>}
        </div>
      </div>
      <div className="data-card wide">
        <span className="data-label">yönlendirme zinciri</span>
        {redirects.length ? redirects.map((item, index) => (
          <p key={`${item.url}-${index}`}>{item.status}: {item.url} → {item.destination}</p>
        )) : <p>yönlendirme gözlenmedi.</p>}
      </div>
      <div className="data-card wide">
        <span className="data-label">sunucunun bildirdiği teknoloji ipuçları</span>
        {technologies.length ? technologies.map((item, index) => (
          <p key={`${item.name}-${index}`}>{item.name}: {item.value} (yanıt başlığından)</p>
        )) : <p>yanıt başlıklarında teknoloji bilgisi bulunmadı; bu, sitede teknoloji olmadığı anlamına gelmez.</p>}
      </div>
    </div>
  );
}

export default function App() {
  const [url, setUrl] = useState('');
  const [scan, setScan] = useState<Scan | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!scan || !['queued', 'running'].includes(scan.status)) return;
    let active = true;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`/api/scans/${scan.id}`, { cache: 'no-store' });
        if (!response.ok) throw new Error('tarama durumu alınamadı.');
        const updated: Scan = await response.json();
        if (active) setScan(updated);
      } catch {
        if (active) setError('tarama durumu alınamadı; bağlantı kurulunca yeniden denenecek.');
      }
    }, 1400);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [scan?.id, scan?.status]);

  async function startScan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    setScan(null);
    try {
      const response = await fetch('/api/scans', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? 'tarama başlatılamadı.');
      setScan(data as Scan);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'beklenmeyen bir hata oluştu.');
    } finally {
      setSubmitting(false);
    }
  }

  const active = scan && ['queued', 'running'].includes(scan.status);
  const verdictClass = scan?.overall_verdict ?? 'unknown';

  return (
    <main className="shell">
      <header className="hero">
        <p className="eyebrow">bağlantı güvenlik kontrolü</p>
        <h1>bir bağlantı hakkında<br />gerçek bilgileri gör.</h1>
        <p className="intro">bilinen tehdit servislerinden alınan sonuçları ve bağlantının teknik yanıtını tek yerde incele. sonuç yoksa bunu açıkça söyleriz; tahmin üretmeyiz.</p>
      </header>

      <section className="scan-card">
        <form onSubmit={startScan}>
          <label htmlFor="url-input">kontrol etmek istediğin bağlantı</label>
          <div className="input-row">
            <input
              id="url-input"
              name="url"
              type="url"
              required
              maxLength={2048}
              placeholder="https://ornek.com"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              autoComplete="url"
            />
            <button type="submit" disabled={submitting || Boolean(active)}>
              {submitting ? 'başlatılıyor…' : active ? 'kontrol ediliyor…' : 'bağlantıyı kontrol et'}
            </button>
          </div>
        </form>
        <p className="privacy-note">gönderdiğin bağlantı tarama geçmişine kaydedilir ve anahtarı ayarlı olan güvenlik servisleriyle paylaşılır. parola sıfırlama kodu gibi özel bilgi içeren bağlantıları gönderme.</p>
        {error && <p className="error" role="alert">{error}</p>}
      </section>

      {scan && (
        <section className="result-section" aria-live="polite">
          <div className="result-heading">
            <div>
              <p className="eyebrow">tarama {scan.id.slice(0, 8)}</p>
              <h2>{scan.status === 'completed' ? 'kontrol tamamlandı' : scan.status === 'failed' ? 'kontrol tamamlanamadı' : 'bağlantı kontrol ediliyor'}</h2>
            </div>
            <span className={`pill ${scan.status}`}>{label(scan.status)}</span>
          </div>
          <div className={`verdict ${verdictClass}`}>
            <span>genel değerlendirme</span>
            <strong>{label(scan.overall_verdict)}</strong>
            <p>{scan.overall_verdict === 'unknown'
              ? 'henüz güvenilir bir sağlayıcı sonucu yok. bu, bağlantının güvenli olduğu anlamına gelmez.'
              : 'bu özet yalnızca aşağıda listelenen gerçek sağlayıcı yanıtlarına dayanıyor.'}</p>
          </div>
          {scan.deduplicated && <p className="muted">aynı bağlantı için devam eden tarama bulundu; mevcut işi gösteriyoruz.</p>}
          {scan.error_message && <p className="error">{scan.error_message}</p>}

          <section className="panel">
            <h3>güvenlik servisleri</h3>
            <p className="muted">servisler ayrı değerlendirilir. yanıt vermeyen veya ayarlanmamış bir servis temiz sonucu sayılmaz.</p>
            <div className="provider-list">
              {scan.providers.length ? scan.providers.map((provider) => (
                <article className="provider-card" key={provider.provider}>
                  <div className="provider-title">
                    <h4>{providerNames[provider.provider] ?? provider.provider.toLowerCase()}</h4>
                    <span className={`pill ${provider.verdict}`}>{label(provider.verdict)}</span>
                  </div>
                  <p>{providerSummary(provider)}</p>
                  <span className="provider-status">durum: {label(provider.status)}</span>
                  {Object.keys(provider.details).length > 0 && (
                    <details>
                      <summary>servis yanıtının ayrıntıları</summary>
                      <pre>{JSON.stringify(provider.details, null, 2)}</pre>
                    </details>
                  )}
                </article>
              )) : <p className="muted">tarama işi kuyruğa alındı; servis sonuçları bekleniyor.</p>}
            </div>
          </section>

          <section className="panel">
            <h3>bağlantı bilgileri</h3>
            <p className="muted">yalnızca gerçekten ölçülebilen bilgiler gösterilir. yanıt içeriği saklanmaz.</p>
            <MetadataPanel metadata={scan.metadata} />
          </section>
        </section>
      )}
      <footer>beta · yerel geliştirme · production yayını yapılmadı</footer>
    </main>
  );
}
