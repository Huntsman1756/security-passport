import { describe, expect, it } from "vitest";
import { checkIsin, isinCheckDigit } from "../lib/isin";

describe("checkIsin", () => {
  it.each(["DE000A3LJCB4", "US0378331005", "IE00B4L5Y983", "ES0113900J37", "XS2081615473"])(
    "accepts %s",
    (isin) => expect(checkIsin(isin)).toEqual({ ok: true, isin }),
  );

  it("normalizes spaces and case", () => {
    expect(checkIsin(" de000a3ljcb4 ")).toEqual({ ok: true, isin: "DE000A3LJCB4" });
  });

  it("rejects a wrong check digit and says which one is expected", () => {
    const r = checkIsin("DE000A3LJCB0");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toContain("4");
  });

  it("rejects wrong length and shape", () => {
    expect(checkIsin("DE000").ok).toBe(false);
    expect(checkIsin("1E00B4L5Y983").ok).toBe(false);
  });

  it("computes the check digit for letter-heavy bodies", () => {
    expect(isinCheckDigit("IE00B4L5Y98")).toBe(3);
  });
});
