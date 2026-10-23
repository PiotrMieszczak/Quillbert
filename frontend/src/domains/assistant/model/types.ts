/** Shapes the panel renders. The backend's wire shapes stay in api/ (ADR-0015). */

export type Citation = {
  label: string;
  /** The campaign document the passage came from; the chip opens it in Documents.
   *  Null for a shared-library passage, which has no document here. */
  documentId: string | null;
  filename: string;
  page: number | null;
  heading: string | null;
  attribution: string | null;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  /** The retrieval step's label, e.g. "Searched 2 documents · 6 passages". Live replies only. */
  searched?: string;
  /** Set only on the live reply: `waiting` (nothing arrived yet), `streaming`, then `done` until the
   *  stored history replaces it. Unset for history, which renders without animation. */
  phase?: "waiting" | "streaming" | "done";
};
