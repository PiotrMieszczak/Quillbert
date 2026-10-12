import type { LibraryDocument } from "./types";

/** Placeholder data from the design prototype until #21 serves real documents. */
export const DOCUMENTS: LibraryDocument[] = [
  { id: "1", name: "Core Rulebook v3.pdf", kind: "PDF", pages: 412, meta: "stat blocks · rules", status: "Indexed", progress: 100 },
  { id: "2", name: "Ashfall Reach — Module.pdf", kind: "PDF", pages: 88, meta: "adventure · maps", status: "Indexed", progress: 100 },
  { id: "3", name: "Bestiary — Regional.pdf", kind: "PDF", pages: 156, meta: "extracting stat blocks", status: "Processing", progress: 64 },
  { id: "4", name: "House Rules.md", kind: "DOC", pages: 6, meta: "table notes", status: "Indexed", progress: 100 },
  { id: "5", name: "Faction Ledger.png", kind: "IMG", pages: 1, meta: "awaiting OCR", status: "Queued", progress: 0 },
];
