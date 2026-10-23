import type { Character, Faction } from "./types";

/** Placeholder data until the cast API exists. Replaced by TanStack Query hooks in
 *  api/ — the views' props do not change when that lands. */

export const NPCS: Character[] = [
  {
    id: "n1",
    name: "Doran Vey",
    role: "Human Smuggler",
    level: 5,
    relationship: "ally",
    location: "Market Row",
    tags: ["Informant", "Docks"],
    player: null,
  },
  {
    id: "n2",
    name: "Serrin of the Hollow",
    role: "Elf Envoy",
    level: 9,
    relationship: "enemy",
    location: "Old Quarter",
    tags: ["Pale Court", "Diplomat"],
    player: null,
  },
  {
    id: "n3",
    name: "Maren Ashdown",
    role: "Retired Captain",
    level: 7,
    relationship: "family",
    location: "Harbour Watch",
    tags: ["Mentor"],
    player: null,
  },
  {
    id: "n4",
    name: "Quill Ostrander",
    role: "Archivist",
    level: 3,
    relationship: "professional",
    location: "The Drowned Archive",
    tags: ["Scholar", "Maps"],
    player: null,
  },
  {
    id: "n5",
    name: "The Lantern Keeper",
    role: "Unknown",
    level: null,
    relationship: "neutral",
    location: null,
    tags: ["Mystery"],
    player: null,
  },
];

export const PLAYERS: Character[] = [
  {
    id: "p1",
    name: "Brother Aldric",
    role: "Human Cleric",
    level: 6,
    relationship: "ally",
    location: "The Party",
    tags: ["Healer", "Faith"],
    player: { playerName: "Sam", class: "Cleric", race: "Human" },
  },
  {
    id: "p2",
    name: "Kestrel",
    role: "Halfling Rogue",
    level: 6,
    relationship: "ally",
    location: "The Party",
    tags: ["Scout"],
    player: { playerName: "Jo", class: "Rogue", race: "Halfling" },
  },
  {
    id: "p3",
    name: "Ysolde Marr",
    role: "Tiefling Warlock",
    level: 5,
    relationship: "ally",
    location: "The Party",
    tags: ["Pact", "Arcana"],
    player: { playerName: "Alex", class: "Warlock", race: "Tiefling" },
  },
];

export const FACTIONS: Faction[] = [
  {
    id: "f1",
    name: "The Pale Court",
    type: "Hidden cabal",
    relationship: "enemy",
    influence: "High",
    motto: "What is buried, rules.",
    memberCount: 12,
  },
  {
    id: "f2",
    name: "Saltmarch Guild",
    type: "Merchant guild",
    relationship: "professional",
    influence: "Medium",
    motto: "Every tide has a price.",
    memberCount: 34,
  },
  {
    id: "f3",
    name: "The Harbour Watch",
    type: "City militia",
    relationship: "ally",
    influence: "Medium",
    motto: null,
    memberCount: 60,
  },
  {
    id: "f4",
    name: "Lantern Choir",
    type: "Religious order",
    relationship: "neutral",
    influence: "Unknown",
    motto: "We keep the light for those who return.",
    memberCount: 7,
  },
];
