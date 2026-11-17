import { useQuery } from "@tanstack/react-query";
import { ApiError, apiFetch } from "../../../lib/api";
import type { Sheet } from "../model/types";

/** A system's character sheet, or null when none is saved: the stat block is then left out
 *  (ADR-0030). The wire shape is the model; sheets are data the admin wrote, shown as written. */
export function useSheet(systemId: string | undefined) {
  return useQuery({
    queryKey: ["cast", "sheet", systemId],
    queryFn: async (): Promise<Sheet | null> => {
      try {
        return (await apiFetch<Sheet>(`/systems/${encodeURIComponent(systemId!)}/sheet`)).data;
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    enabled: systemId !== undefined,
    // Reference data: an admin changes it rarely.
    staleTime: 5 * 60 * 1000,
  });
}
