import { useEffect, useRef } from "react";
import type { Message } from "../../model/types";
import { MessageBubble } from "../MessageBubble";
import styles from "./MessageList.module.css";

type MessageListProps = {
  messages: Message[];
  /** Show the intro message: the conversation is empty and nothing is loading. */
  intro: boolean;
  error?: string;
  onRetry: () => void;
  onEditQuestion: () => void;
  onOpenSource: (documentId: string) => void;
  onAddDocuments: () => void;
};

/** A constant, not stored: it makes no model call (docs/design/overview.md → AI panel). */
const INTRO: Message = {
  id: "intro",
  role: "assistant",
  content:
    "I'm Quillbert. Ask me about your rulebooks and campaign notes — I answer from what you've uploaded, cite the page, and tell you when something isn't there.",
  citations: [],
};

export function MessageList({ messages, intro, error, onRetry, onEditQuestion, onOpenSource, onAddDocuments }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [messages, error]);

  return (
    <div className={styles.list}>
      {intro && <MessageBubble message={INTRO} onOpenSource={onOpenSource} onAddDocuments={onAddDocuments} />}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} onOpenSource={onOpenSource} onAddDocuments={onAddDocuments} />
      ))}
      {error && (
        <div className={styles.error} role="alert">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
            <circle cx="8" cy="8" r="6.5" />
            <path d="M8 4.8v3.6M8 11h.01" strokeLinecap="round" />
          </svg>
          <div className={styles.errorBody}>
            <div className={styles.errorTitle}>Quillbert couldn’t finish that answer</div>
            <div className={styles.errorText}>{error}</div>
            <div className={styles.errorActions}>
              <button type="button" className={styles.retry} onClick={onRetry}>
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden>
                  <path d="M2.5 7a4.5 4.5 0 1 0 1.4-3.3M2.5 2v2.6h2.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Retry
              </button>
              <button type="button" className={styles.edit} onClick={onEditQuestion}>
                Edit question
              </button>
            </div>
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
