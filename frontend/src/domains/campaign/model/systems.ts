/** How each system looks in the picker. Values are palette tokens from docs/design/reference.md,
 *  as hex because the tint is stored on the campaign. Unknown systems fall back to the accent. */
const LOOK: Record<string, { tint: string; edition: string }> = {
  "dnd-2014": { tint: "#EF7777", edition: "5e · 2014 rules" },
  "dnd-2024": { tint: "#E8B87A", edition: "5e · 2024 revision" },
  "traveller-2e": { tint: "#7BA3D6", edition: "Mongoose 2nd ed." },
};

export const tintFor = (systemId: string) => LOOK[systemId]?.tint ?? "#E8B87A";
export const editionFor = (systemId: string) => LOOK[systemId]?.edition ?? "Ruleset";

/** The banner formats the API accepts, and its size limit. */
export const BANNER_TYPES = ["image/png", "image/jpeg", "image/webp"];
export const BANNER_MAX_BYTES = 10 * 1024 * 1024;
