/** A document in the campaign's library. Mirrors docs/data-model.md Document. */

export type DocumentKind = "PDF" | "DOC" | "IMG";

export type DocumentStatus = "Indexed" | "Processing" | "Queued";

export type LibraryDocument = {
  id: string;
  name: string;
  kind: DocumentKind;
  /** Unknown until extraction counts them. */
  pages: number | null;
  meta: string;
  status: DocumentStatus;
  /** 0–100 */
  progress: number;
};
