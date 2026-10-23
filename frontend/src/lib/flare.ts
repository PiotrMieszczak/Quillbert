/** Window event the ambient background listens for; `detail.ms` is how long it stays bright. */
export const FLARE_EVENT = "quill:flare";

/** Brighten the ambient background and spin its gears for `ms` (Quillbert at work). */
export function flare(ms: number) {
  window.dispatchEvent(new CustomEvent(FLARE_EVENT, { detail: { ms } }));
}
