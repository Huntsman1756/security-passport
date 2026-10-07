import { useEffect, useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";

function ThemeToggle() {
  const [dark, setDark] = useState(
    () => document.documentElement.classList.contains("dark"),
  );
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);
  return (
    <button
      onClick={() => setDark(!dark)}
      className="rounded border border-[var(--line)] px-2 py-1 text-[12px] text-[var(--ink-2)] hover:bg-[var(--surface-2)]"
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? "◐ light" : "◑ dark"}
    </button>
  );
}

export function App() {
  const [q, setQ] = useState("");
  const nav = useNavigate();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const v = q.trim().toUpperCase();
    if (v.length === 12) {
      setQ("");
      nav(`/isin/${v}`);
    }
  };
  return (
    <div className="min-h-screen bg-[var(--surface)] text-[var(--ink)]">
      <nav className="sticky top-0 z-40 border-b border-[var(--line)] bg-[var(--surface)]/90 backdrop-blur">
        <div className="mx-auto flex h-12 max-w-5xl items-center gap-4 px-4">
          <Link
            to="/"
            className="text-[14px] font-semibold tracking-tight"
          >
            Security Passport
          </Link>
          <form onSubmit={submit} className="ml-auto hidden sm:block">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="ISIN"
              maxLength={12}
              spellCheck={false}
              className="mono h-7.5 w-44 rounded border border-[var(--line)] bg-[var(--surface-2)] px-2.5 text-[12px] tracking-wider outline-none focus:border-[var(--accent)]"
              aria-label="ISIN search"
            />
          </form>
          <Link
            to="/sources"
            className="text-[12.5px] text-[var(--ink-2)] hover:text-[var(--ink)]"
          >
            Sources
          </Link>
          <ThemeToggle />
        </div>
      </nav>
      <Outlet />
      <footer className="border-t border-[var(--line)] py-6">
        <div className="mx-auto max-w-5xl px-4 text-[11.5px] leading-relaxed text-[var(--ink-2)]">
          Security Passport transforms and combines public source
          information — not endorsed by ESMA, ECB, GLEIF, ISO/SWIFT,
          or BME/Iberclear.{" "}
          <Link to="/sources" className="underline">
            Source attribution
          </Link>
          . Every field carries provenance; unknown is a valid
          result.
        </div>
      </footer>
    </div>
  );
}
