import { useState, useEffect, useRef } from "react";
import "./App.css";

const API = "http://localhost:8000";
const APP_NAME = "NextCinema"; 

function Poster({ src, title }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return (
      <div className="noimg">
        <span>🎬</span>
        <p>{title}</p>
      </div>
    );
  }
  return <img src={src} alt={title} loading="lazy" onError={() => setFailed(true)} />;
}

function MovieCard({ m, onPick }) {
  return (
    <div className="card" onClick={() => onPick(m.title)}>
      <div className="posterbox">
        <Poster src={m.poster} title={m.title} />
        {m.rating != null && <span className="badge rating">⭐ {m.rating}</span>}
        {m.match != null && <span className="badge match">{Math.round(m.match * 100)}%</span>}
      </div>
      <div className="info">
        <strong>{m.title}</strong>
        <span className="muted">{m.year ?? "n/a"}</span>
      </div>
    </div>
  );
}

export default function App() {
  const [q, setQ] = useState("");
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [recs, setRecs] = useState([]);
  const [popular, setPopular] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const skip = useRef(false);

  useEffect(() => {
    document.title = APP_NAME;
    fetch(`${API}/popular?n=20`).then((r) => r.json()).then(setPopular).catch(() => {});
  }, []);

  useEffect(() => {
    if (skip.current) { skip.current = false; return; }
    if (q.length < 2) { setOptions([]); return; }
    const t = setTimeout(() => {
      fetch(`${API}/search?q=${encodeURIComponent(q)}`)
        .then((r) => r.json()).then(setOptions).catch(() => {});
    }, 200);
    return () => clearTimeout(t);
  }, [q]);

  async function pick(title) {
    skip.current = true;
    setQ(title);
    setOptions([]);
    setLoading(true);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
    try {
      const res = await fetch(`${API}/recommend?title=${encodeURIComponent(title)}&n=10`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setSelected(data.movie);
      setRecs(data.recommendations);
    } catch {
      setError("Could not load recommendations. Is the API running on port 8000?");
    }
    setLoading(false);
  }

  async function submit(e) {
    e.preventDefault();
    if (!q.trim()) return;
    try {
      const res = await fetch(`${API}/search?q=${encodeURIComponent(q.trim())}`);
      const hits = await res.json();
      if (hits.length) pick(hits[0].title);
      else { setOptions([]); setError(`No movie found for "${q}".`); }
    } catch {
      setError("Could not reach the API. Is it running on port 8000?");
    }
  }

  // goes back to the home page: clears the search, the selected movie and any errors
  function goHome() {
    skip.current = true;
    setSelected(null);
    setRecs([]);
    setQ("");
    setOptions([]);
    setError("");
    setLoading(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <>
      <header className="top">
        <button type="button" className="logo" onClick={goHome} title="Go to home page">
          🎬 {APP_NAME}
        </button>
        <form className="search" onSubmit={submit}>
          <div className="field">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search for a movie you like..."
              autoComplete="off"
            />
            {options.length > 0 && (
              <ul>
                {options.map((o) => (
                  <li key={o.title} onClick={() => pick(o.title)}>
                    <div className="thumb"><Poster src={o.poster} title="" /></div>
                    <span>{o.title}</span>
                    <small className="muted">{o.year ?? ""}</small>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <button type="submit">🔍 Search</button>
        </form>
      </header>

      <main className="app">
        {error && <p className="error">{error}</p>}
        {loading && <p className="muted">Finding movies...</p>}

        {!selected && !loading && (
          <>
            <h3>🔥 Top rated — click one to get recommendations</h3>
            <div className="grid">
              {popular.map((m) => <MovieCard key={m.title} m={m} onPick={pick} />)}
            </div>
          </>
        )}

        {selected && !loading && (
          <>
            <button className="back" onClick={goHome}>← Back to home</button>
            <div className="hero">
              <div className="heroimg"><Poster src={selected.poster} title={selected.title} /></div>
              <div>
                <h2>{selected.title} <span className="muted">({selected.year ?? "n/a"})</span></h2>
                <p className="muted">⭐ {selected.rating} · {selected.genres}</p>
                <p>{selected.overview}</p>
              </div>
            </div>
            <h3>You might also like</h3>
            <div className="grid">
              {recs.map((r) => <MovieCard key={r.title} m={r} onPick={pick} />)}
            </div>
          </>
        )}
      </main>
    </>
  );
}