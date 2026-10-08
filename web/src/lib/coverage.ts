import type { FieldStatus, Passport, PassportField } from "../types";
import { STATUS_ORDER } from "./statusMeta";

const BLOCKS = [
  "identity",
  "primary_market",
  "secondary_market",
  "post_trade",
  "eurosystem_collateral",
] as const;

function isField(v: unknown): v is PassportField {
  return !!v && typeof v === "object" && "status" in v;
}

export function countStatuses(p: Passport): Record<FieldStatus, number> {
  const out = Object.fromEntries(STATUS_ORDER.map((s) => [s, 0])) as Record<
    FieldStatus,
    number
  >;
  for (const b of BLOCKS)
    for (const v of Object.values(p[b])) if (isField(v)) out[v.status] += 1;
  return out;
}
