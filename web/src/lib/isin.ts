/** Client-side ISIN check (ISO 6166): structure + Luhn check digit
 * over the letter-expanded body. Mirrors domain/isin.py so the UI
 * can reject typos before a round-trip; the API stays the
 * authority. */
const SHAPE = /^[A-Z]{2}[A-Z0-9]{9}[0-9]$/;

export function normalizeIsin(raw: string): string {
  return raw.replace(/[\s-]/g, "").toUpperCase();
}

export function isinCheckDigit(body11: string): number {
  const digits = [...body11]
    .map((c) => (c >= "A" ? String(c.charCodeAt(0) - 55) : c))
    .join("");
  let sum = 0;
  let double = true; // rightmost body digit sits left of the check digit
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = Number(digits[i]);
    if (double) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    sum += d;
    double = !double;
  }
  return (10 - (sum % 10)) % 10;
}

export type IsinCheck =
  | { ok: true; isin: string }
  | { ok: false; reason: string };

export function checkIsin(raw: string): IsinCheck {
  const isin = normalizeIsin(raw);
  if (isin.length !== 12)
    return { ok: false, reason: `ISINs have 12 characters (got ${isin.length}).` };
  if (!SHAPE.test(isin))
    return {
      ok: false,
      reason: "Expected 2-letter country prefix, 9 alphanumerics, 1 check digit.",
    };
  const expected = isinCheckDigit(isin.slice(0, 11));
  if (expected !== Number(isin[11]))
    return { ok: false, reason: `Check digit should be ${expected}.` };
  return { ok: true, isin };
}
