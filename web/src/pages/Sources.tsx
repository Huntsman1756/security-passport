const SOURCES = [
  {
    name: "ESMA FIRDS (via OpenInstrument)",
    use: "Instrument identity, CFI/FISN, venue listings, issuer assertions, publication history",
    legal: "ESMA Registers Legal Notice — reproduction authorised with source acknowledgment and transformation notice",
    basis: "reconstructed (provider publication time)",
  },
  {
    name: "ESMA Prospectus Register (PRIII)",
    use: "Prospectus document graph, approval and passporting metadata",
    legal: "ESMA Registers Legal Notice",
    basis: "observed history",
  },
  {
    name: "ECB eligible marketable assets",
    use: "Collateral eligibility, haircut inputs, reported issuer CSD",
    legal: "ECB public list — attribution; transformed projection",
    basis: "current snapshot",
  },
  {
    name: "ECB eligible SSSs / eligible links",
    use: "Eurosystem settlement-system topology",
    legal: "ECB public operational documentation",
    basis: "observed history",
  },
  {
    name: "GLEIF (via OpenInstrument)",
    use: "ISIN↔LEI mapping, legal entity identity",
    legal: "CC0",
    basis: "reconstructed",
  },
  {
    name: "ISO 10383 MIC list",
    use: "Venue MIC naming",
    legal: "Public registry (SWIFT registration authority)",
    basis: "observed history",
  },
  {
    name: "Iberclear (BME) public documentation",
    use: "SSS identity only — no instrument-level claims",
    legal: "Public documentation",
    basis: "curated",
  },
];

export function Sources() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-2xl font-semibold">Sources & attribution</h1>
      <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-[var(--ink-2)]">
        Security Passport transforms and combines public source
        information. It is not endorsed by ESMA, the ECB, GLEIF,
        ISO/SWIFT, or BME/Iberclear.
      </p>
      <div className="mt-8 space-y-4">
        {SOURCES.map((s) => (
          <section
            key={s.name}
            className="rounded-lg border border-[var(--line)] p-4"
          >
            <h2 className="text-[14px] font-semibold">{s.name}</h2>
            <div className="mt-2 grid gap-x-8 gap-y-1 text-[13px] sm:grid-cols-[8rem_1fr]">
              <span className="text-[var(--ink-2)]">Used for</span>
              <span>{s.use}</span>
              <span className="text-[var(--ink-2)]">Legal basis</span>
              <span>{s.legal}</span>
              <span className="text-[var(--ink-2)]">
                Temporal basis
              </span>
              <span className="mono">{s.basis}</span>
            </div>
          </section>
        ))}
      </div>
      <p className="mt-8 text-[12.5px] leading-relaxed text-[var(--ink-2)]">
        ESMA sources: source — European Securities and Markets
        Authority (ESMA), ESMA Registers. Security Passport
        transforms and combines the original REGISTERS information.
        ECB: source — European Central Bank, published collateral
        lists and operational documentation; data shown is a
        transformed projection with per-field retrieval metadata.
      </p>
    </div>
  );
}
