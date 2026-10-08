import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, ScrollRestoration } from "react-router-dom";
import { IsinSearch } from "./components/IsinSearch";
import { useServiceStatus } from "./lib/status";

import { REPO_URL } from "./lib/links";

function readTheme(): boolean {
  return document.documentElement.classList.contains("dark");
}

function ThemeToggle() {
  const [dark, setDark] = useState(readTheme);
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("theme", dark ? "dark" : "light");
    } catch {
      /* storage unavailable — theme still applies for this view */
    }
  }, [dark]);
  return (
    <button
      onClick={() => setDark(!dark)}
      className="grid h-8 w-8 place-items-center rounded-md border border-[var(--line)] text-[13px] text-[var(--ink-2)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)]"
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      title={dark ? "Light theme" : "Dark theme"}
    >
      {dark ? "☀" : "☾"}
    </button>
  );
}

export function Logo() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden>
      <rect x="3" y="2.5" width="18" height="19" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M7.5 8h9M7.5 12h6M7.5 16h3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="16.5" cy="16" r="1.6" fill="var(--accent)" />
    </svg>
  );
}

const navCls = ({ isActive }: { isActive: boolean }) =>
  `text-[13px] transition ${isActive ? "text-[var(--ink)]" : "text-[var(--ink-2)] hover:text-[var(--ink)]"}`;

function DemoRibbon() {
  const st = useServiceStatus();
  const demo = st.data?.demo;
  if (!demo) return null;
  return (
    <div className="border-b border-[var(--line)] bg-[var(--accent-soft)] text-[12px] text-[var(--ink-2)]">
      <div className="mx-auto max-w-6xl px-4 py-1.5">
        <strong className="font-medium text-[var(--ink)]">Demo instance.</strong>{" "}
        Replays a captured corpus of {demo.corpus.length} instruments
        {demo.captured_at ? ` (captured ${demo.captured_at})` : ""} through the
        production parsers.{" "}
        <Link to="/corpus" className="underline underline-offset-2 hover:text-[var(--ink)]">
          Browse the corpus
        </Link>
      </div>
    </div>
  );
}

export function App() {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--surface)] text-[var(--ink)]">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-[var(--surface)] focus:px-3 focus:py-1.5">
        Skip to content
      </a>
      <nav className="sticky top-0 z-40 border-b border-[var(--line)] bg-[var(--surface)]/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-5 px-4">
          <Link to="/" className="flex items-center gap-2 text-[14px] font-semibold tracking-tight">
            <Logo />
            Security Passport
          </Link>
          <div className="ml-auto hidden w-52 md:block">
            <IsinSearch size="sm" />
          </div>
          <div className="ml-auto flex items-center gap-4 md:ml-0">
            <NavLink to="/corpus" className={navCls}>Corpus</NavLink>
            <NavLink to="/sources" className={navCls}>Sources</NavLink>
            <a href="/api/docs" className="hidden text-[13px] text-[var(--ink-2)] hover:text-[var(--ink)] sm:inline">API</a>
            <a href={REPO_URL} className="hidden text-[13px] text-[var(--ink-2)] hover:text-[var(--ink)] sm:inline">GitHub</a>
            <ThemeToggle />
          </div>
        </div>
      </nav>
      <DemoRibbon />
      <main id="main" className="flex-1">
        <Outlet />
      </main>
      <ScrollRestoration />
      <footer className="border-t border-[var(--line)] py-8">
        <div className="mx-auto grid max-w-6xl gap-4 px-4 text-[12px] leading-relaxed text-[var(--ink-2)] sm:grid-cols-[1fr_auto]">
          <p className="max-w-2xl">
            Security Passport transforms and combines public source information.
            It is not endorsed by ESMA, the ECB, GLEIF, ISO/SWIFT or
            BME/Iberclear, and it is not investment, legal or settlement advice.{" "}
            <Link to="/sources" className="underline underline-offset-2">Attribution</Link>.
          </p>
          <p className="sm:text-right">
            Open source (MIT) ·{" "}
            <a href={REPO_URL} className="underline underline-offset-2">Huntsman1756/security-passport</a>
          </p>
        </div>
      </footer>
    </div>
  );
}
