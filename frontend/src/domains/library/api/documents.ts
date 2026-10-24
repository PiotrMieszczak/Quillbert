import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../../lib/api";
import type { DocumentStatus, LibraryDocument } from "../model/types";

/** The backend's document (docs/api-contract.md → Documents). Stays inside api/ (ADR-0015).
 *  shortcut: written by hand; generate it from openapi.json once the type generator lands. */
type DocumentDto = {
  id: number;
  filename: string;
  kind: LibraryDocument["kind"];
  pageCount: number | null;
  meta: string | null;
  status: "queued" | "processing" | "indexed" | "failed" | "awaiting_ocr";
  progress: number;
  error: string | null;
  /** Library only (ADR-0027): systems it applies to; empty means all. */
  systems: string[];
};

const STATUS: Record<DocumentDto["status"], DocumentStatus> = {
  queued: "Queued",
  processing: "Processing",
  indexed: "Indexed",
  failed: "Failed",
  awaiting_ocr: "Awaiting OCR",
};

const toDocument = (dto: DocumentDto): LibraryDocument => ({
  id: String(dto.id),
  name: dto.filename,
  kind: dto.kind,
  pages: dto.pageCount,
  meta: dto.status === "failed" ? (dto.error ?? "extraction failed") : (dto.meta ?? "waiting for extraction"),
  status: STATUS[dto.status],
  progress: dto.progress,
  systems: dto.systems ?? [],
});

/** Which shelf (ADR-0027): a campaign's documents, or the signed-in GM's library. */
export type DocumentSource = { campaignId: string } | "library";

const documentsPath = (source: DocumentSource) =>
  typeof source === "string" ? `/${source}/documents` : `/campaigns/${encodeURIComponent(source.campaignId)}/documents`;

export const documentsKey = (source: DocumentSource) =>
  ["documents", typeof source === "string" ? source : source.campaignId] as const;

const moving = (documents: LibraryDocument[] | undefined) =>
  documents?.some((document) =>
    document.status === "Queued" ||
    document.status === "Processing" ||
    document.status === "Awaiting OCR",
  ) ?? false;

/** A shelf's documents. Polls while anything is queued, processing, or awaiting OCR, then stops. */
export function useDocuments(source: DocumentSource) {
  return useQuery({
    queryKey: documentsKey(source),
    queryFn: async () => (await apiFetch<DocumentDto[]>(documentsPath(source))).data.map(toDocument),
    refetchInterval: (query) => (moving(query.state.data) ? 4000 : false),
  });
}

/** Tags for a library upload; a campaign upload ignores them. */
export type UploadTags = { systems?: string[] };

/** `duplicate` is true when the shelf already had these bytes (the API answers 200, not 202).
 *  Aborting `signal` cancels the upload. */
export async function uploadDocument(source: DocumentSource, file: File, tags: UploadTags = {}, signal?: AbortSignal) {
  const form = new FormData();
  form.append("file", file);
  if (typeof source === "string") form.append("systems", (tags.systems ?? []).join(","));
  const { status, data } = await apiFetch<DocumentDto>(documentsPath(source), { method: "POST", body: form, signal });
  return { document: toDocument(data), duplicate: status === 200 };
}

/** Removes the document and its stored file. */
export async function deleteDocument(source: DocumentSource, documentId: string) {
  await apiFetch<null>(`${documentsPath(source)}/${encodeURIComponent(documentId)}`, { method: "DELETE" });
}
