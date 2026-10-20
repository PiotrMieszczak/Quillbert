import type { ActivityEntry, Campaign, CampaignStats } from "./types";

/** Placeholder data until the API exists. Replaced by TanStack Query hooks in
 *  api/ — the view's props do not change when that lands. */

export const CAMPAIGN: Campaign = {
  id: "ashfall",
  name: "The Ashfall Compact",
  system: "D&D 2024",
  tint: "#E8B87A",
  imageUrl: null,
  sessionCount: 14,
};

export const STATS: CampaignStats = {
  npcs: 38,
  factions: 6,
  activeQuests: 4,
  documents: 12,
};

export const ACTIVITY: ActivityEntry[] = [
  {
    id: "a1",
    kind: "session",
    title: "Session 14 — The Pale Court receives them",
    detail: "3h 20m · the party bargained instead of fighting",
    at: "2 days ago",
  },
  {
    id: "a2",
    kind: "npc",
    title: "Doran Vey",
    detail: "Disposition moved from neutral to ally",
    at: "2 days ago",
  },
  {
    id: "a3",
    kind: "quest",
    title: "The Drowned Archive",
    detail: "Moved to in progress · 2 of 5 subquests",
    at: "5 days ago",
  },
  {
    id: "a4",
    kind: "document",
    title: "Bestiary — Regional.pdf",
    detail: "156 pages indexed",
    at: "1 week ago",
  },
  {
    id: "a5",
    kind: "npc",
    title: "Serrin of the Hollow",
    detail: "Added to the cast · faction Pale Court",
    at: "1 week ago",
  },
];
