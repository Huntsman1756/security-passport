import { useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { status } from "../api";

export const CorpusEntry = z.object({
  isin: z.string(),
  name: z.string().nullable(),
  cfi: z.string().nullable(),
});
export type CorpusEntry = z.infer<typeof CorpusEntry>;

export const ServiceStatus = z.object({
  version: z.string(),
  provider_mode: z.string(),
  generation: z.string().nullable(),
  openinstrument_generation: z.string().nullable(),
  demo: z
    .object({
      corpus: z.array(CorpusEntry),
      captured_at: z.string().nullable(),
    })
    .nullable()
    .optional(),
});
export type ServiceStatus = z.infer<typeof ServiceStatus>;

/** Service status, shared across pages (one fetch per session). */
export function useServiceStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: async () => ServiceStatus.parse(await status()),
    staleTime: Infinity,
  });
}
