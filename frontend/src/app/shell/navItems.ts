/** Workspace destinations, in the order docs/design/overview.md specifies.
 *  The rail and the mobile tab bar both read this one list. */
export type NavItem = {
  id: string;
  label: string;
  glyph: string;
  /** Shorter label for the tab bar, where space is tight. */
  short?: string;
  /** The view exists. Unbuilt destinations stay hidden rather than lead to placeholders. */
  built?: boolean;
};

const ALL_ITEMS: NavItem[] = [
  { id: "overview", label: "Overview", glyph: "◇", short: "Home" },
  { id: "npcs", label: "NPCs", glyph: "☾" },
  { id: "players", label: "Players", glyph: "✦", short: "Party" },
  { id: "factions", label: "Factions", glyph: "⌘" },
  { id: "quests", label: "Quest Log", glyph: "✧", short: "Quests" },
  { id: "documents", label: "Documents", glyph: "▤", built: true },
  { id: "graph", label: "Knowledge Graph", glyph: "⊛" },
  { id: "sessions", label: "Sessions", glyph: "❍" },
];

export const NAV_ITEMS = ALL_ITEMS.filter((item) => item.built);

/** The tab bar's first choices; other built views fill any free tab before More. */
export const TAB_IDS = ["overview", "npcs", "players", "quests"];
export const TAB_COUNT = 4;
