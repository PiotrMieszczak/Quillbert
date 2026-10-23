import type { LibraryDocument } from "./types";

/** A picked file as a row while its upload is in flight, or after it was refused. */
export function pendingFromFile(file: File, id: string, error?: string): LibraryDocument {
  return {
    id,
    name: file.name,
    kind: file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC",
    pages: null,
    meta: error ?? "uploading…",
    status: error ? "Failed" : "Uploading",
    progress: 0,
    systems: [],
    attribution: null,
  };
}
