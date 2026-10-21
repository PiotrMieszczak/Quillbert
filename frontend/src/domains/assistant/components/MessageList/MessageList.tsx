import { useEffect, useRef } from "react";
import type { Message } from "../../model/types";
import { MessageBubble } from "../MessageBubble";
import styles from "./MessageList.module.css";

type MessageListProps = {
  messages: Message[];
  /** Show the intro bubble: the conversation is empty and nothing is loading. */
  intro: boolean;
  error?: string;
  onRetry: () => void;
};

/** A constant, not stored: it makes no model call (docs/design/overview.md → AI panel). */
const INTRO: Message = {
  id: "intro",
  role: "assistant",
  content:
    "I'm Quillbert. Ask me about your rulebooks and campaign notes — I answer from what you've uploaded, cite the page, and tell you when something isn't there.",
  citations: [],
};

export function MessageList({ messages, intro, error, onRetry }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView();
  }, [messages, error]);

  return (
    <div className={styles.list}>
      {intro && <MessageBubble message={INTRO} />}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {error && (
        <p className={styles.error} role="alert">
          {error}{" "}
          <button type="button" className={styles.retry} onClick={onRetry}>
            Retry
          </button>
        </p>
      )}
      <div ref={endRef} />
    </div>
  );
}
