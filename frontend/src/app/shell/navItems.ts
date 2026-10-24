/** Workspace destinations, in the order docs/design/overview.md specifies.
 *  The rail and the mobile tab bar both read this one list. */
export type NavItem = {
  id: string;
  label: string;
  /** Shorter label for the tab bar, where space is tight. */
  short?: string;
  /** The view exists. Unbuilt destinations stay hidden rather than lead to placeholders. */
  built?: boolean;
};

const ALL_ITEMS: NavItem[] = [
  { id: "overview", label: "Overview", short: "Home" },
  { id: "npcs", label: "NPCs" },
  { id: "players", label: "Players", short: "Party" },
  { id: "factions", label: "Factions" },
  { id: "quests", label: "Quest Log", short: "Quests" },
  { id: "documents", label: "Documents", built: true },
  { id: "graph", label: "Knowledge Graph" },
  { id: "sessions", label: "Sessions" },
];

export const NAV_ITEMS = ALL_ITEMS.filter((item) => item.built);

/** The tab bar's first choices; other built views fill any free tab before More. */
export const TAB_IDS = ["overview", "npcs", "players", "quests"];
export const TAB_COUNT = 4;
