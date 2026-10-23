/** A document on a shelf: a campaign or a GM's library. Mirrors docs/data-model.md Document. */

export type DocumentKind = "PDF" | "DOC" | "IMG";

/** "Uploading" exists only in the browser, before the API has the file. */
export type DocumentStatus =
  | "Indexed"
  | "Processing"
  | "Queued"
  | "Failed"
  | "Uploading"
  | "Awaiting OCR";

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
  /** Systems a library document applies to; empty means all. */
  systems: string[];
};
