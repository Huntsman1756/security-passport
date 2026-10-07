import { z } from "zod";

export const FieldStatus = z.enum([
  "reported",
  "derived",
  "inferred",
  "not_found",
  "not_applicable",
  "conflict",
]);
export type FieldStatus = z.infer<typeof FieldStatus>;

export const EvidenceRef = z.object({
  provider: z.string(),
  dataset: z.string(),
  record_id: z.string(),
  artifact_id: z.string().default(""),
  source_locator: z.string().default(""),
  retrieved_at: z.string().default(""),
  published_at: z.string().default(""),
  effective_at: z.string().default(""),
  raw_value: z.unknown().optional(),
  parser_version: z.string().default(""),
  transformations: z.array(z.string()).default([]),
  upstream: z
    .object({
      provider: z.string(),
      artifact: z.string(),
      locator: z.string(),
    })
    .optional(),
});
export type EvidenceRef = z.infer<typeof EvidenceRef>;

export const RuleRef = z.object({
  rule_id: z.string(),
  rule_version: z.number(),
  inputs: z.array(z.record(z.string(), z.unknown())).default([]),
  basis: z.string().default(""),
  limitations: z.string().default(""),
});

export const Alternative = z.object({
  value: z.unknown(),
  role: z.string().default(""),
  evidence: EvidenceRef,
});

export const Temporal = z.object({
  basis: z.string(),
  coverage_start: z.string().nullable().default(null),
  coverage_end: z.string().nullable().default(null),
  left_censored: z.boolean().default(false),
  source_time_semantics: z.string().default(""),
});

export const PassportField = z.object({
  value: z.unknown().optional(),
  status: FieldStatus,
  evidence: z.array(EvidenceRef).default([]),
  rule: RuleRef.optional(),
  quality_flags: z.array(z.string()).default([]),
  temporal: Temporal.optional(),
  alternatives: z.array(Alternative).default([]),
  searched_sources: z.array(z.string()).default([]),
  explanation: z.string().default(""),
  raw_value: z.unknown().optional(),
  unit: z.string().default(""),
});
export type PassportField = z.infer<typeof PassportField>;

export const Listing = z.object({
  venue_mic: z.string(),
  venue_name: z.string().default(""),
  venue_mic_status: z.string().default(""),
  oprt_sgmt: z.string().default(""),
  relevant_venue: z.string().default(""),
  relevant_venue_name: z.string().default(""),
  issuer_requested_admission: z.string().default(""),
  admission_approval_date: z.string().nullable().default(null),
  admission_approval_date_raw: z.unknown().optional(),
  first_trade_date: z.string().nullable().default(null),
  first_trade_date_raw: z.unknown().optional(),
  termination_date: z.string().nullable().default(null),
  termination_date_raw: z.unknown().optional(),
  state: z.string(),
  quality_flags: z.array(z.string()).default([]),
  evidence: EvidenceRef.optional(),
  mic_evidence: EvidenceRef.nullable().optional(),
});
export type Listing = z.infer<typeof Listing>;

export const DocNode = z.object({
  root_id: z.string(),
  document_type: z.string(),
  document_type_descr: z.string(),
  prospectus_type: z.string(),
  structure_type: z.string(),
  national_document_id: z.string(),
  home_member_state: z.string(),
  member_states: z.array(z.string()),
  is_passported: z.boolean(),
  approval_filing_date: z.string(),
  first_passporting_date: z.string(),
  doc_last_update_date: z.string(),
  download_url: z.string(),
  party_name: z.string(),
  issuer_lei: z.string(),
  issuer_name: z.string(),
  offeror_lei: z.string(),
  offeror_name: z.string(),
  related_document_ids: z.array(z.string()),
  languages: z.string(),
  status: z.string(),
  observed_at: z.string(),
});
export type DocNode = z.infer<typeof DocNode>;

const Block = z
  .record(z.string(), z.unknown())
  .transform((r) => r as Record<string, PassportField | unknown> & {
    listings?: Listing[];
    document_graph?: DocNode[];
    entity_roles?: { role: string; lei: string; source: string }[];
    identifiers?: {
      level: string; scheme: string; value: string; provider: string;
    }[];
    eligible_sss?: {
      name: string; country: string; status: string;
      evidence?: EvidenceRef;
    }[];
    link_topology?: {
      investor_csd: string; issuer_csd: string;
      link_type: string; intermediaries: string[];
      operated_by: string; status: string;
      evidence?: EvidenceRef;
    }[];
    settlement_locations?: {
      csd: string; csd_code: string | null;
      relationship: string; mic: string; market: string;
      settlement_currency: string;
      source_published_at: string;
      effective_from: string | null; note: string | null;
      status: string; provider: string;
      evidence?: EvidenceRef;
    }[];
    route_assessments?: {
      from_sss: string | null; to_sss: string | null;
      status: string; assessment: string;
      explanation: string; rule: string;
      limitations: string;
      evidence?: EvidenceRef | null;
    }[];
    temporal?: z.infer<typeof Temporal>;
    warnings?: string[];
  });

export const Passport = z.object({
  schema_version: z.string(),
  passport_id: z.string(),
  isin: z.string(),
  valid_checksum: z.boolean(),
  generated_at: z.string(),
  generation: z.string(),
  openinstrument_generation: z.string(),
  overall_state: z.string(),
  identity: Block,
  primary_market: Block,
  secondary_market: Block,
  post_trade: Block,
  eurosystem_collateral: Block,
  temporal_coverage: z.record(z.string(), z.unknown()),
  source_summary: z.array(z.record(z.string(), z.unknown())),
  warnings: z.array(z.string()).default([]),
});
export type Passport = z.infer<typeof Passport>;
export type PassportBlock = z.infer<typeof Block>;

export const SearchResult = z.object({
  query: z.string(),
  results: z.array(
    z.object({
      isin: z.string(),
      full_name: z.string().nullable(),
      cfi: z.string().nullable(),
      kind: z.string().default(""),
    }),
  ),
});

export const ApiError = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.unknown().optional(),
    request_id: z.string().optional(),
  }),
});
