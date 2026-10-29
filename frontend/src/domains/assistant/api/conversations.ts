import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../../lib/api";
import type { Citation, Message } from "../model/types";

/** docs/api-contract.md → Assistant. Stays inside api/ (ADR-0015).
 *  shortcut: written by hand; generate it from openapi.json once the type generator lands. */
type ConversationDto = {
  id: number;
  campaignId: string;
  mode: string;
  startedAt: string;
};

export type CitationDto = {
  label: string;
  chunkId: number;
  documentId: number;
  filename: string;
  pageFrom: number | null;
  heading: string | null;
  attribution: string | null;
};

type MessageDto = {
  id: number;
  role: Message["role"];
  content: string;
  createdAt: string;
  toolLabel: string | null;
  refused: boolean;
  citations: CitationDto[];
};

/** Also the shape of the `dm.citation` custom event's value (docs/api-contract.md → Streaming response). */
export const toCitation = (dto: CitationDto): Citation => ({
  label: dto.label,
  documentId: String(dto.documentId),
  filename: dto.filename,
  page: dto.pageFrom,
  heading: dto.heading,
  attribution: dto.attribution,
});

const toMessage = (dto: MessageDto): Message => ({
  id: String(dto.id),
  role: dto.role,
  content: dto.content,
  citations: dto.citations.map(toCitation),
  searched: dto.toolLabel ?? undefined,
  refused: dto.refused,
});

const conversationsPath = (campaignId: string) => `/campaigns/${encodeURIComponent(campaignId)}/conversations`;

export const messagesPath = (campaignId: string, conversationId: number) =>
  `${conversationsPath(campaignId)}/${conversationId}/messages`;

export const conversationsKey = (campaignId: string) => ["conversations", campaignId] as const;

export const messagesKey = (campaignId: string, conversationId: number) =>
  [...conversationsKey(campaignId), conversationId, "messages"] as const;

/** The campaign's conversations, newest first. */
export function useConversations(campaignId: string) {
  return useQuery({
    queryKey: conversationsKey(campaignId),
    queryFn: async () => (await apiFetch<ConversationDto[]>(conversationsPath(campaignId))).data,
  });
}

/** A conversation's history; `conversationId` is null before the first send. */
export function useMessages(campaignId: string, conversationId: number | null) {
  return useQuery({
    queryKey: messagesKey(campaignId, conversationId ?? 0),
    queryFn: async () =>
      (await apiFetch<MessageDto[]>(messagesPath(campaignId, conversationId!))).data.map(toMessage),
    enabled: conversationId !== null,
  });
}

export async function createConversation(campaignId: string) {
  const { data } = await apiFetch<ConversationDto>(conversationsPath(campaignId), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  return data;
}
