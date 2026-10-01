import './style.css';

export default function App() {
  return (
    <main className="shell">
      <header>
        <p className="eyebrow">Defensive URL intelligence</p>
        <h1>URL Security Scanner</h1>
        <p className="intro">
          A privacy-conscious reputation analysis platform. No scan providers are
          connected in this development baseline.
        </p>
      </header>
      <section className="notice" role="status">
        <strong>Live scanning is not available yet.</strong>
        <p>
          No URL has been submitted to a security provider and no verdict has been
          produced. This interface will only show findings returned by real,
          attributed providers after the integrations are configured.
        </p>
      </section>
      <section className="roadmap">
        <h2>Platform status</h2>
        <ul>
          <li>API health and input validation scaffold: available</li>
          <li>Provider-backed URL analysis: not implemented</li>
          <li>Database persistence and asynchronous worker: not implemented</li>
        </ul>
      </section>
      <footer>Development scaffold · No production deployment</footer>
    </main>
  );
}
