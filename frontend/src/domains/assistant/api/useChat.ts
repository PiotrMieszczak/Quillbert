import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import type { Citation, Message } from "../model/types";
import { conversationsKey, createConversation, useConversations, useMessages } from "./conversations";
import { sendMessage } from "./run";

/** The reply in flight, until the stored history replaces it. */
type Run = {
  question: string;
  status: "waiting" | "streaming" | "done" | "error";
  text: string;
  searched?: string;
  citations: Citation[];
  error?: string;
};

/** One campaign's assistant panel: the open conversation's history plus the reply being streamed.
 *  Opens the newest conversation; the first send creates one if there is none. */
export function useChat(campaignId: string) {
  const queryClient = useQueryClient();
  const conversations = useConversations(campaignId);
  // undefined follows the newest conversation, null is a blank new one, a number is a chosen/created one.
  const [selected, setSelected] = useState<number | null | undefined>(undefined);
  const conversationId = selected === undefined ? (conversations.data?.[0]?.id ?? null) : selected;
  const history = useMessages(campaignId, conversationId);
  const [run, setRun] = useState<Run | null>(null);
  const generation = useRef(0);
  const abortRun = useRef<(() => void) | null>(null);

  /** Drops the reply in flight, e.g. when the panel closes or a new conversation starts. */
  const abort = useCallback(() => {
    generation.current++;
    // The server may have stored the question before the abort landed.
    if (abortRun.current) void queryClient.invalidateQueries({ queryKey: conversationsKey(campaignId) });
    abortRun.current?.();
    abortRun.current = null;
    setRun(null);
  }, [campaignId, queryClient]);

  useEffect(() => () => {
    generation.current++;
    abortRun.current?.();
  }, []);

  const send = useCallback(
    async (content: string) => {
      const gen = ++generation.current;
      const live = () => generation.current === gen;
      const patch = (changes: Partial<Run>) => live() && setRun((current) => current && { ...current, ...changes });
      let failed = false;
      const fail = (message: string) => {
        failed = true;
        patch({ status: "error", error: message });
      };

      setRun({ question: content, status: "waiting", text: "", citations: [] });
      let id = conversationId;
      if (id === null) {
        try {
          id = (await createConversation(campaignId)).id;
        } catch (error) {
          fail(error instanceof Error ? error.message : "Couldn’t start a conversation.");
          return;
        }
        if (!live()) return;
        setSelected(id);
      }

      const sending = sendMessage(campaignId, id, content, {
        onSearched: (searched) => patch({ status: "streaming", searched }),
        onText: (text) => patch({ status: "streaming", text }),
        onCitation: (citation) => live() && setRun((current) => current && { ...current, citations: [...current.citations, citation] }),
        onError: fail,
      });
      abortRun.current = sending.abort;
      await sending.done;
      if (live()) abortRun.current = null;
      if (failed || !live()) return;
      patch({ status: "done" });
      // Keep the live reply on screen until the stored one has loaded, so nothing flickers.
      await queryClient.invalidateQueries({ queryKey: conversationsKey(campaignId) });
      if (live()) setRun(null);
    },
    [campaignId, conversationId, queryClient],
  );

  const newConversation = useCallback(() => {
    abort();
    setSelected(null);
  }, [abort]);

  /** Drops the failed run and hands its question back for editing. */
  const editLast = useCallback(() => {
    const question = run?.status === "error" ? run.question : "";
    setRun(null);
    return question;
  }, [run]);

  const messages: Message[] = [...(history.data ?? [])];
  if (run) {
    messages.push({ id: "live-question", role: "user", content: run.question, citations: [] });
    if (run.status !== "error") {
      messages.push({
        id: "live-reply",
        role: "assistant",
        content: run.text,
        citations: run.citations,
        searched: run.searched,
        phase: run.status,
      });
    }
  }

  return {
    messages,
    /** The history is still loading for an existing conversation. */
    loading: conversations.isPending || (conversationId !== null && history.isPending),
    sending: run !== null && run.status !== "error",
    error: run?.status === "error" ? run.error : undefined,
    empty: messages.length === 0,
    canReset: conversationId !== null || run !== null,
    send,
    retry: () => (run ? send(run.question) : undefined),
    editLast,
    abort,
    newConversation,
  };
}
