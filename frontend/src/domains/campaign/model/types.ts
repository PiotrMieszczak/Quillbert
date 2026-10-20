/** Shapes the campaign views render. Mirrors docs/data-model.md, narrowed to what
 *  the views need; api/ maps the wire DTOs onto these. */

export type Campaign = {
  id: string;
  name: string;
  /** Display name, e.g. "D&D 2014". */
  system: string;
  /** Hex accent for the badge and the placeholder banner. */
  tint: string;
  /** Full API path of the banner, or null for the tint gradient. */
  imageUrl: string | null;
  sessionCount: number;
};

export type GameSystem = {
  id: string;
  name: string;
};

export type CampaignStats = {
  npcs: number;
  factions: number;
  activeQuests: number;
  documents: number;
};

export type ActivityKind = "session" | "npc" | "quest" | "document";

export type ActivityEntry = {
  id: string;
  kind: ActivityKind;
  title: string;
  detail: string;
  at: string;
};
