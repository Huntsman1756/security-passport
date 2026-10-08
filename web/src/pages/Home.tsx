import { Link } from "react-router-dom";
import { IsinSearch } from "../components/IsinSearch";
import { StatusBadge } from "../components/StatusBadge";
import { STATUS_META, STATUS_ORDER } from "../lib/statusMeta";
import { REPO_URL } from "../lib/links";

/** Curated entry points: each one demonstrates a property of the
 * evidence model, not just "an instrument". */
const SHOWCASE: {
  isin: string;
  asOf?: string;
  title: string;
  kind: string;
  shows: string;
}[] = [
  {
    isin: "IE00B4L5Y983",
    asOf: "2026-09-19",
    title: "iShares Core MSCI World",
    kind: "ETF · as of 19 Sep 2026",
    shows: "Temporal semantics: the settlement document is published, but the location is not yet effective.",
  },
  {
    isin: "IE0007SRI1C7",
    title: "iShares V (EUR acc.)",
    kind: "ETF share class",
    shows: "A preserved conflict: providers disagree on the issuer LEI, and both assertions are shown.",
  },
  {
    isin: "DE000A3LJCB4",
    title: "EPH Group 10% 2030",
    kind: "Corporate bond",
    shows: "A full passport: prospectus chain, venue admissions and Eurosystem collateral data.",
  },
  {
    isin: "ES0105321030",
    title: "Accion EuroStoxx 50 ETF",
    kind: "Spanish ETF",
    shows: "Fund roles from the CNMV register, kept as an upstream artifact reference.",
  },
  {
    isin: "FR0000120271",
    title: "TotalEnergies SE",
    kind: "Equity",
    shows: "Instrument-level settlement evidence: issuer CSD plus a designated place of settlement effective from 21 Sep 2026.",
  },
  {
    isin: "FR0129714681",
    title: "ECB-listed asset",
    kind: "Partial record",
    shows: "Unknown is a valid result: only the ECB list knows it, and the passport says exactly that.",
  },
];

const BLOCKS = [
  {
    name: "Identity",
    q: "What is it?",
    body: "CFI, FISN, issuer LEI with preserved conflicts, currency, maturity, competent authority.",
    src: "ESMA FIRDS · GLEIF",
  },
  {
    name: "Primary market",
    q: "Which documents support it?",
    body: "Prospectus, base prospectus, final terms and supplements as a document graph, with passporting.",
    src: "ESMA Prospectus Register",
  },
  {
    name: "Secondary market",
    q: "Where is it admitted to trading?",
    body: "ISIN × MIC admissions with admission, first-trade and termination state.",
    src: "ESMA FIRDS · ISO 10383",
  },
  {
    name: "Post-trade",
    q: "How could it settle?",
    body: "Issuer CSD, instrument-level settlement locations, CSD link topology and route assessments, kept as four separate claims.",
    src: "ECB · Euronext · Iberclear",
  },
  {
    name: "Eurosystem collateral",
    q: "Is it eligible collateral?",
    body: "Eligibility, haircut category and inputs, and the exact ECB snapshot the claim comes from.",
    src: "ECB eligible assets",
  },
];

const PRINCIPLES = [
  ["Unknown is a valid result", "Absence is not_found, never false, unless an authoritative enumeration plus a versioned rule justify the derivation."],
  ["Conflicts are preserved", "When sources disagree, every assertion is shown. Nothing is silently adjudicated."],
  ["No invented routes", "A link between two settlement systems does not prove an ISIN can settle across it, and the passport says so."],
  ["Release gate: zero unsupported assertions", "A golden corpus is rebuilt on every change. Any field without evidence or a rule blocks the release."],
];

export function Home() {
  return (
    <div>
      {/* hero */}
      <section className="hero-grid border-b border-[var(--line)]">
        <div className="mx-auto max-w-6xl px-4 pb-14 pt-16 sm:pt-24">
          <p className="mono text-[11.5px] uppercase tracking-[0.2em] text-[var(--accent)]">
            European securities · public data · field-level provenance
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
            Every claim about a security, with its receipt.
          </h1>
          <p className="mt-5 max-w-2xl text-[16px] leading-relaxed text-[var(--ink-2)]">
            Security Passport turns an ISIN into an operational record:
            identity, prospectus chain, trading venues, settlement evidence
            and Eurosystem collateral status. Every field states whether it
            was reported, derived or inferred, and links to the source
            record behind it.
          </p>
          <div className="mt-8">
            <IsinSearch />
          </div>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-[12.5px] text-[var(--ink-2)]">
            <a href="/api/docs" className="underline-offset-2 hover:text-[var(--ink)] hover:underline">REST API (OpenAPI) →</a>
            <a href={REPO_URL} className="underline-offset-2 hover:text-[var(--ink)] hover:underline">Source code →</a>
            <Link to="/corpus" className="underline-offset-2 hover:text-[var(--ink)] hover:underline">All demo instruments →</Link>
          </div>
        </div>
      </section>

      {/* showcase */}
      <section className="mx-auto max-w-6xl px-4 py-14">
        <SectionTitle eyebrow="Start here" title="Six passports, six properties of the model" />
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SHOWCASE.map((e) => (
            <Link
              key={e.isin + (e.asOf ?? "")}
              to={`/isin/${e.isin}${e.asOf ? `?as_of=${e.asOf}` : ""}`}
              className="group flex flex-col rounded-lg border border-[var(--line)] p-4 transition hover:border-[var(--accent)] hover:bg-[var(--surface-2)]"
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className="mono text-[13px] font-semibold tracking-wide">{e.isin}</span>
                <span className="text-[11px] text-[var(--ink-2)]">{e.kind}</span>
              </div>
              <div className="mt-1 text-[14px] font-medium">{e.title}</div>
              <p className="mt-2 flex-1 text-[13px] leading-relaxed text-[var(--ink-2)]">{e.shows}</p>
              <span className="mt-3 text-[12px] text-[var(--accent)] group-hover:underline">Open passport →</span>
            </Link>
          ))}
        </div>
      </section>

      {/* blocks */}
      <section className="border-y border-[var(--line)] bg-[var(--surface-2)]">
        <div className="mx-auto max-w-6xl px-4 py-14">
          <SectionTitle eyebrow="What a passport answers" title="Five questions, each with its own sources" />
          <div className="mt-6 grid gap-px overflow-hidden rounded-lg border border-[var(--line)] bg-[var(--line)] sm:grid-cols-2 lg:grid-cols-5">
            {BLOCKS.map((b) => (
              <div key={b.name} className="flex flex-col bg-[var(--surface)] p-4">
                <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--ink-2)]">{b.name}</div>
                <div className="mt-2 text-[15px] font-medium">{b.q}</div>
                <p className="mt-2 flex-1 text-[12.5px] leading-relaxed text-[var(--ink-2)]">{b.body}</p>
                <div className="mono mt-3 text-[10.5px] text-[var(--ink-3)]">{b.src}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* evidence model */}
      <section className="mx-auto grid max-w-6xl gap-10 px-4 py-14 lg:grid-cols-2">
        <div>
          <SectionTitle eyebrow="Evidence model" title="Six states. Every field has exactly one." />
          <dl className="mt-6 space-y-3">
            {STATUS_ORDER.map((s) => (
              <div key={s} className="grid grid-cols-[7.5rem_1fr] items-baseline gap-3">
                <dt><StatusBadge status={s} /></dt>
                <dd className="text-[13px] leading-relaxed text-[var(--ink-2)]">{STATUS_META[s].meaning}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div>
          <SectionTitle eyebrow="Design rules" title="What it will not do" />
          <ul className="mt-6 space-y-4">
            {PRINCIPLES.map(([t, d]) => (
              <li key={t} className="border-l-2 border-[var(--accent)] pl-4">
                <div className="text-[14px] font-medium">{t}</div>
                <p className="mt-1 text-[13px] leading-relaxed text-[var(--ink-2)]">{d}</p>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-[12.5px] leading-relaxed text-[var(--ink-2)]">
            No prices, portfolios, alerts or chat. Read-only, built on public
            European registers. See the{" "}
            <a className="underline underline-offset-2" href={`${REPO_URL}/tree/main/docs/adr`}>architecture decision records</a>.
          </p>
        </div>
      </section>
    </div>
  );
}

function SectionTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <div className="mono text-[11px] uppercase tracking-[0.2em] text-[var(--ink-3)]">{eyebrow}</div>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight">{title}</h2>
    </div>
  );
}
