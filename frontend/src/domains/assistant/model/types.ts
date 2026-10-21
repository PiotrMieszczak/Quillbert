/** Shapes the panel renders. The backend's wire shapes stay in api/ (ADR-0015). */

export type Citation = {
  label: string;
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
  /** The retrieval step's green check row, e.g. "Searched 2 documents · 6 passages". Live replies only. */
  searched?: string;
  /** `waiting` shows the typing dots (nothing arrived yet); `streaming` shows the cursor. */
  phase?: "waiting" | "streaming";
};
