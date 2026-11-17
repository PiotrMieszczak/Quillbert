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

/** A faction as the form edits it: blank text is "", never null. */
export type FactionDraft = {
  name: string;
  relationship: Relationship;
  type: string;
  influence: string;
  reach: string;
  motto: string;
  goal: string;
  notes: string;
};

export type Faction = FactionDraft & { id: string };

export const FACTION_TEXT = ["type", "influence", "reach", "motto", "goal", "notes"] as const;

export const emptyFaction = (): FactionDraft => ({
  name: "",
  relationship: "neutral",
  type: "",
  influence: "",
  reach: "",
  motto: "",
  goal: "",
  notes: "",
});

/** A system's character sheet (ADR-0030): what the stat block holds. */
export type SheetField = {
  key: string;
  label: string;
  type: "int" | "text" | "list";
  min?: number;
  max?: number;
  /** Columns of a repeating row; only on a list field. */
  itemFields?: SheetField[];
};

export type Sheet = { sections: { key: string; label: string; fields: SheetField[] }[] };

export type StatRow = Record<string, number | string>;
export type StatValue = number | string | StatRow[];
/** Keyed by the sheet's section, then field. */
export type Stats = Record<string, Record<string, StatValue>>;

export const PROFILE_FIELDS = ["playerName", "class", "race", "background", "xp", "pronouns", "bonds"] as const;

/** A character as the form edits it: blank text is "", never null. */
export type CharacterDraft = {
  name: string;
  isPlayer: boolean;
  relationship: Relationship;
  role: string;
  level: number | null;
  location: string;
  disposition: string;
  lastSeen: string;
  tags: string[];
  quote: string;
  notes: string;
  bio: string;
  stats: Stats;
  /** Sent only for a player character. */
  profile: Record<(typeof PROFILE_FIELDS)[number], string>;
};

export type CharacterDetail = CharacterDraft & { id: string };

export const emptyDraft = (isPlayer: boolean): CharacterDraft => ({
  name: "",
  isPlayer,
  relationship: isPlayer ? "ally" : "neutral",
  role: "",
  level: null,
  location: "",
  disposition: "",
  lastSeen: "",
  tags: [],
  quote: "",
  notes: "",
  bio: "",
  stats: {},
  profile: { playerName: "", class: "", race: "", background: "", xp: "", pronouns: "", bonds: "" },
});
