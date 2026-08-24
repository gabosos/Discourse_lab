export default function Home() {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <p className="eyebrow">Discourse Lab</p>
        <h1>Aprende lingüística y discurso organizacional con experiencias gamificadas</h1>
        <p>Una plataforma educativa profesional diseñada para estudiantes, docentes y equipos.</p>
        <div className="hero-actions">
          <a className="btn primary" href="/dashboard">Ir al panel</a>
          <a className="btn secondary" href="/levels">Explorar niveles</a>
        </div>
      </section>
    </main>
  );
}
