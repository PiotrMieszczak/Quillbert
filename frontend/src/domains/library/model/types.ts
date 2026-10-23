/** A document on a shelf: a campaign, a GM's library, or the vault. Mirrors docs/data-model.md Document. */

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
  /** Systems a library or vault document applies to; empty means all. */
  systems: string[];
  /** Vault licence line, e.g. "SRD 5.2 · CC-BY-4.0". */
  attribution: string | null;
};
