import { HttpAgent } from "@ag-ui/client";
import { accessToken } from "../../../lib/api";
import type { Citation } from "../model/types";
import { messagesPath, toCitation, type CitationDto } from "./conversations";

export type RunHandlers = {
  /** Retrieval finished, e.g. "Searched 2 documents · 6 passages". */
  onSearched: (label: string) => void;
  /** The reply so far. */
  onText: (text: string) => void;
  onCitation: (citation: Citation) => void;
  onError: (message: string) => void;
};

/** Sends `content` as the user's turn and streams the reply (docs/api-contract.md → Assistant).
 *  `done` resolves when the run ends, however it ends; failures go to `onError`. `abort` is usable
 *  immediately, before the token fetch finishes, and silences the handlers. */
export function sendMessage(campaignId: string, conversationId: number, content: string, handlers: RunHandlers) {
  let agent: HttpAgent | undefined;
  let aborted = false;

  const done = (async () => {
    const token = await accessToken();
    if (aborted) return;
    agent = new HttpAgent({
      url: `/api/v1${messagesPath(campaignId, conversationId)}`,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      threadId: String(conversationId),
      initialMessages: [{ id: crypto.randomUUID(), role: "user", content }],
    });

    let text = "";
    let failure: string | undefined;
    let finished = false;
    try {
      await agent.runAgent(
        {},
        {
          onTextMessageContentEvent: ({ event }) => {
            if (aborted) return;
            text += event.delta;
            handlers.onText(text);
          },
          onToolCallResultEvent: ({ event }) => {
            if (!aborted && typeof event.content === "string") handlers.onSearched(event.content);
          },
          onCustomEvent: ({ event }) => {
            if (!aborted && event.name === "dm.citation") handlers.onCitation(toCitation(event.value as CitationDto));
          },
          onRunFinishedEvent: () => {
            finished = true;
          },
          onRunErrorEvent: ({ event }) => {
            failure = event.message;
          },
        },
      );
      // The client resolves on RUN_ERROR and on a dropped stream; only the network failing rejects.
      if (!aborted && !finished) handlers.onError(failure ?? "The connection dropped before the reply finished.");
    } catch (error) {
      if (!aborted) handlers.onError(failure ?? (error instanceof Error ? error.message : "Something went wrong."));
    }
  })();

  return {
    done,
    abort: () => {
      aborted = true;
      agent?.abortRun();
    },
  };
}
