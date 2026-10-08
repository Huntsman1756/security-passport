import { describe, expect, it } from "vitest";
import { countStatuses } from "../lib/coverage";
import type { Passport } from "../types";

const f = (status: string) => ({ status, value: null });

describe("countStatuses", () => {
  it("counts field statuses across all blocks and ignores non-field keys", () => {
    const p = {
      identity: { cfi: f("reported"), lei: f("conflict"), entity_roles: [] },
      primary_market: { prospectus_found: f("not_found") },
      secondary_market: { listing_count: f("derived"), listings: [] },
      post_trade: { assessment: f("inferred"), temporal: { basis: "x" } },
      eurosystem_collateral: { eligible: f("reported") },
    } as unknown as Passport;
    expect(countStatuses(p)).toEqual({
      reported: 2, derived: 1, inferred: 1, conflict: 1,
      not_found: 1, not_applicable: 0,
    });
  });
});
