import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../../lib/api";
import { FACTION_TEXT, type Faction, type FactionDraft, type Relationship } from "../model/types";

/** The backend's faction (docs/api-contract.md → Factions). Stays inside api/ (ADR-0015).
 *  shortcut: written by hand; generate it from openapi.json once the type generator lands (#153). */
export type FactionDto = { id: number; name: string; relationship: Relationship } & Record<
  (typeof FACTION_TEXT)[number],
  string | null
>;

export const toFaction = (dto: FactionDto): Faction => ({
  id: String(dto.id),
  name: dto.name,
  relationship: dto.relationship,
  ...(Object.fromEntries(FACTION_TEXT.map((key) => [key, dto[key] ?? ""])) as Pick<Faction, (typeof FACTION_TEXT)[number]>),
});

/** The body for POST and PATCH alike: blank text is sent as null, which a PATCH reads as "clear". */
export const toFactionBody = (draft: FactionDraft) => ({
  name: draft.name.trim(),
  relationship: draft.relationship,
  ...Object.fromEntries(FACTION_TEXT.map((key) => [key, draft[key].trim() || null])),
});

export const factionsKey = (campaignId: string) => ["cast", "factions", campaignId] as const;

const factionPath = (campaignId: string, id?: string) =>
  `/campaigns/${encodeURIComponent(campaignId)}/factions${id ? `/${encodeURIComponent(id)}` : ""}`;

/** A campaign's factions, by name. The list carries every field, so the detail page reads from it. */
export function useFactions(campaignId: string) {
  return useQuery({
    queryKey: factionsKey(campaignId),
    queryFn: async () => (await apiFetch<FactionDto[]>(factionPath(campaignId))).data.map(toFaction),
  });
}

/** Creates the faction when `id` is null, otherwise replaces its editable fields. */
export async function saveFaction(campaignId: string, id: string | null, draft: FactionDraft) {
  const { data } = await apiFetch<FactionDto>(factionPath(campaignId, id ?? undefined), {
    method: id ? "PATCH" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toFactionBody(draft)),
  });
  return toFaction(data);
}

export async function deleteFaction(campaignId: string, id: string) {
  await apiFetch(factionPath(campaignId, id), { method: "DELETE" });
}
