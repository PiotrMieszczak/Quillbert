import { useQuery } from "@tanstack/react-query";
import { apiBlob, apiFetch } from "../../../lib/api";
import type { Campaign, GameSystem } from "../model/types";

/** The backend's campaign and system (docs/api-contract.md → Campaigns). Stay inside api/ (ADR-0015).
 *  shortcut: written by hand; generate them from openapi.json once the type generator lands. */
type SystemDto = { id: string; name: string };

type CampaignDto = {
  id: string;
  name: string;
  system: SystemDto;
  tint: string;
  imageUrl: string | null;
  sessionCount: number;
  lastPlayedAt: string | null;
};

const toCampaign = (dto: CampaignDto): Campaign => ({
  id: dto.id,
  name: dto.name,
  system: dto.system.name,
  tint: dto.tint,
  imageUrl: dto.imageUrl,
  sessionCount: dto.sessionCount,
});

export const campaignsKey = ["campaigns"] as const;

/** The signed-in user's campaigns, most recently played first. */
export function useCampaigns() {
  return useQuery({
    queryKey: campaignsKey,
    queryFn: async () => (await apiFetch<CampaignDto[]>("/campaigns")).data.map(toCampaign),
  });
}

/** The systems a new campaign can be played in. Reference data: fetched once per session. */
export function useSystems() {
  return useQuery({
    queryKey: ["systems"],
    queryFn: async (): Promise<GameSystem[]> => (await apiFetch<SystemDto[]>("/systems")).data,
    staleTime: Infinity,
  });
}

export async function createCampaign(input: { name: string; systemId: string; tint: string }) {
  const { data } = await apiFetch<CampaignDto>("/campaigns", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return toCampaign(data);
}

/** Sets the campaign's banner, replacing any earlier one. */
export async function uploadCampaignImage(campaignId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiFetch<CampaignDto>(`/campaigns/${encodeURIComponent(campaignId)}/image`, {
    method: "POST",
    body: form,
  });
  return toCampaign(data);
}

/** A blob URL for a banner. `imageUrl` carries a version, so a cached blob is never stale.
 *  shortcut: blob URLs are not revoked; there is one per banner, so the leak is a few images. */
export function useCampaignImage(imageUrl: string | null) {
  return useQuery({
    queryKey: ["campaign-image", imageUrl],
    queryFn: async () => URL.createObjectURL(await apiBlob(imageUrl!)),
    enabled: imageUrl !== null,
    staleTime: Infinity,
  });
}
