/** Shapes the cast views render. Mirrors docs/data-model.md (Character, Faction),
 *  narrowed to what the list views need. */

export type Relationship = "ally" | "enemy" | "family" | "professional" | "neutral";

export const RELATIONSHIPS: Relationship[] = ["ally", "enemy", "family", "professional", "neutral"];

/** Colour token per relationship; every view uses this one map. */
export const RELATIONSHIP_TONE: Record<Relationship, string> = {
  ally: "var(--rel-ally)",
  enemy: "var(--rel-enemy)",
  family: "var(--rel-family)",
  professional: "var(--rel-professional)",
  neutral: "var(--rel-neutral)",
};

export type PlayerProfile = {
  playerName: string;
  class: string;
  race: string;
};

export type Character = {
  id: string;
  name: string;
  role: string;
  level: number | null;
  relationship: Relationship;
  location: string | null;
  tags: string[];
  /** Present only for player characters. */
  player: PlayerProfile | null;
};

export type Faction = {
  id: string;
  name: string;
  type: string;
  relationship: Relationship;
  influence: string;
  motto: string | null;
  memberCount: number;
};
