import { useQuery } from "@tanstack/react-query";
import { apiBlob, apiFetch } from "../../../lib/api";
import {
  PROFILE_FIELDS,
  type Character,
  type CharacterDetail,
  type CharacterDraft,
  type Relationship,
  type Stats,
} from "../model/types";

type ProfileDto = Record<(typeof PROFILE_FIELDS)[number], string | null>;

/** The backend's character list row (docs/api-contract.md → Characters). Stays inside api/ (ADR-0015).
 *  shortcut: written by hand; generate it from openapi.json once the type generator lands (#153). */
export type CharacterDto = {
  id: number;
  name: string;
  isPlayer: boolean;
  relationship: Relationship;
  role: string | null;
  level: number | null;
  location: string | null;
  tags: string[];
  portraitUrl: string | null;
  playerProfile: Partial<ProfileDto> | null;
};

type CharacterPageDto = { items: CharacterDto[]; nextCursor: string | null };

export const toCharacter = (dto: CharacterDto): Character => ({
  id: String(dto.id),
  name: dto.name,
  role: dto.role ?? "",
  level: dto.level,
  relationship: dto.relationship,
  location: dto.location,
  tags: dto.tags,
  portraitUrl: dto.portraitUrl,
  player: dto.isPlayer
    ? {
        playerName: dto.playerProfile?.playerName ?? "",
        class: dto.playerProfile?.class ?? "",
        race: dto.playerProfile?.race ?? "",
      }
    : null,
});

export type CharacterFilter = { isPlayer: boolean; relationship?: Relationship | null };

export const charactersKey = (campaignId: string) => ["cast", "characters", campaignId] as const;

/** A campaign's NPCs or player characters, by name. The server filters by relationship.
 *  shortcut: the first 200 only; follow `nextCursor` when a campaign outgrows one page. */
export function useCharacters(campaignId: string, { isPlayer, relationship = null }: CharacterFilter) {
  return useQuery({
    queryKey: [...charactersKey(campaignId), isPlayer, relationship],
    queryFn: async () => {
      const query = new URLSearchParams({ isPlayer: String(isPlayer), limit: "200" });
      if (relationship) query.set("relationship", relationship);
      const path = `/campaigns/${encodeURIComponent(campaignId)}/characters?${query}`;
      return (await apiFetch<CharacterPageDto>(path)).data.items.map(toCharacter);
    },
  });
}

/** The detail adds what a card does not show (docs/api-contract.md → Characters). */
export type CharacterDetailDto = CharacterDto & {
  disposition: string | null;
  lastSeen: string | null;
  quote: string | null;
  notes: string | null;
  bio: string | null;
  stats: Stats;
};

const profileOf = (dto: Partial<ProfileDto> | null) =>
  Object.fromEntries(PROFILE_FIELDS.map((key) => [key, dto?.[key] ?? ""])) as CharacterDraft["profile"];

export const toDetail = (dto: CharacterDetailDto): CharacterDetail => ({
  id: String(dto.id),
  name: dto.name,
  isPlayer: dto.isPlayer,
  relationship: dto.relationship,
  role: dto.role ?? "",
  level: dto.level,
  location: dto.location ?? "",
  disposition: dto.disposition ?? "",
  lastSeen: dto.lastSeen ?? "",
  tags: dto.tags,
  quote: dto.quote ?? "",
  notes: dto.notes ?? "",
  bio: dto.bio ?? "",
  stats: dto.stats,
  portraitUrl: dto.portraitUrl,
  profile: profileOf(dto.playerProfile),
});

const blankToNull = (value: string) => value.trim() || null;

/** The body for POST and PATCH alike: blank text is sent as null, which a PATCH reads as "clear".
 *  An NPC sends no profile: the API refuses one. */
export const toBody = (draft: CharacterDraft) => ({
  name: draft.name.trim(),
  isPlayer: draft.isPlayer,
  relationship: draft.relationship,
  role: blankToNull(draft.role),
  level: draft.level,
  location: blankToNull(draft.location),
  disposition: blankToNull(draft.disposition),
  lastSeen: blankToNull(draft.lastSeen),
  tags: draft.tags,
  quote: blankToNull(draft.quote),
  notes: blankToNull(draft.notes),
  bio: blankToNull(draft.bio),
  stats: draft.stats,
  ...(draft.isPlayer && {
    playerProfile: Object.fromEntries(PROFILE_FIELDS.map((key) => [key, blankToNull(draft.profile[key])])),
  }),
});

const characterPath = (campaignId: string, id?: string) =>
  `/campaigns/${encodeURIComponent(campaignId)}/characters${id ? `/${encodeURIComponent(id)}` : ""}`;

/** One character in full. Its key sits under `charactersKey`, so saving refreshes lists and detail together. */
export function useCharacter(campaignId: string, id: string | null) {
  return useQuery({
    queryKey: [...charactersKey(campaignId), "one", id],
    queryFn: async () => toDetail((await apiFetch<CharacterDetailDto>(characterPath(campaignId, id!))).data),
    enabled: id !== null,
  });
}

/** Creates the character when `id` is null, otherwise replaces its editable fields. `keepStats`
 *  leaves stats out of an edit that did not touch them, so stats saved under an older sheet do not
 *  block renaming the character (ADR-0030 NEG-002). */
export async function saveCharacter(campaignId: string, id: string | null, draft: CharacterDraft, keepStats = false) {
  const { stats, ...rest } = toBody(draft);
  const { data } = await apiFetch<CharacterDetailDto>(characterPath(campaignId, id ?? undefined), {
    method: id ? "PATCH" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(id && keepStats ? rest : { ...rest, stats }),
  });
  return toDetail(data);
}

export async function deleteCharacter(campaignId: string, id: string) {
  await apiFetch(characterPath(campaignId, id), { method: "DELETE" });
}

/** Sets the character's portrait, replacing any earlier one. */
export async function uploadPortrait(campaignId: string, id: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiFetch<CharacterDetailDto>(`${characterPath(campaignId, id)}/portrait`, {
    method: "POST",
    body: form,
  });
  return toDetail(data);
}

/** A blob URL for a portrait: an <img> cannot send the bearer token. `portraitUrl` carries a
 *  version, so a cached blob is never stale.
 *  shortcut: blob URLs are not revoked; there is one per portrait version seen in a session. */
export function usePortrait(portraitUrl: string | null) {
  return useQuery({
    queryKey: ["cast", "portrait", portraitUrl],
    queryFn: async () => URL.createObjectURL(await apiBlob(portraitUrl!)),
    enabled: portraitUrl !== null,
    staleTime: Infinity,
  });
}
