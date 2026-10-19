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
});

const documentsPath = (campaignId: string) => `/campaigns/${encodeURIComponent(campaignId)}/documents`;

export const documentsKey = (campaignId: string) => ["documents", campaignId] as const;

const moving = (documents: LibraryDocument[] | undefined) =>
  documents?.some((document) =>
    document.status === "Queued" ||
    document.status === "Processing" ||
    document.status === "Awaiting OCR",
  ) ?? false;

/** The campaign's library. Polls while anything is queued, processing, or awaiting OCR, then stops. */
export function useDocuments(campaignId: string) {
  return useQuery({
    queryKey: documentsKey(campaignId),
    queryFn: async () => (await apiFetch<DocumentDto[]>(documentsPath(campaignId))).data.map(toDocument),
    refetchInterval: (query) => (moving(query.state.data) ? 4000 : false),
  });
}

/** `duplicate` is true when the campaign already had these bytes (the API answers 200, not 202).
 *  Aborting `signal` cancels the upload. */
export async function uploadDocument(campaignId: string, file: File, signal?: AbortSignal) {
  const form = new FormData();
  form.append("file", file);
  const { status, data } = await apiFetch<DocumentDto>(documentsPath(campaignId), { method: "POST", body: form, signal });
  return { document: toDocument(data), duplicate: status === 200 };
}

/** Removes the document and its stored file. */
export async function deleteDocument(campaignId: string, documentId: string) {
  await apiFetch<null>(`${documentsPath(campaignId)}/${encodeURIComponent(documentId)}`, { method: "DELETE" });
}
