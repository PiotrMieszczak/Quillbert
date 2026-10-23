import { useEffect, useRef, useState } from "react";
import { flare } from "../../../../lib/flare";
import type { Campaign } from "../../../campaign";
import { useChat } from "../../api/useChat";
import { Composer } from "../Composer";
import { MessageList } from "../MessageList";
import styles from "./AssistantPanel.module.css";

/** How long the ambient background stays stoked after a question is sent. */
const SEND_FLARE_MS = 3400;

type AssistantPanelProps = {
  campaign: Campaign;
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
  /** A citation chip was clicked: show that document in the library. */
  onOpenSource: (documentId: string) => void;
};

export function AssistantPanel({ campaign, open, onOpen, onClose, onOpenSource }: AssistantPanelProps) {
  const chat = useChat(campaign.id);
  const { abort } = chat;
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // The panel stays mounted when closed; closing stops the reply in flight.
  useEffect(() => {
    if (!open) abort();
  }, [open, abort]);

  // ⌘K / Ctrl+K opens the panel and puts the cursor in the composer.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== "k" || !(event.metaKey || event.ctrlKey)) return;
      event.preventDefault();
      onOpen();
      // After the panel drops `inert`, which happens on the re-render.
      setTimeout(() => inputRef.current?.focus(), 60);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onOpen]);

  const send = (content: string) => {
    flare(SEND_FLARE_MS);
    void chat.send(content);
  };

  const editQuestion = () => {
    setDraft(chat.editLast());
    inputRef.current?.focus();
  };

  return (
    <section className={styles.panel} aria-label="Quillbert">
      <div className={styles.grabber} aria-hidden />
      <header className={styles.header}>
        <div className={styles.spark} aria-hidden>
          ✦
        </div>
        <div className={styles.titles}>
          <div className={styles.title}>Quillbert</div>
          <div className={styles.subtitle}>Answers from your documents</div>
        </div>
        <button
          type="button"
          className={styles.iconButton}
          aria-label="New conversation"
          title="New conversation"
          disabled={!chat.canReset}
          onClick={chat.newConversation}
        >
          ✎
        </button>
        <button type="button" className={styles.iconButton} aria-label="Close Quillbert" title="Close" onClick={onClose}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
            <path className={styles.collapseIcon} d="M6 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
            <path className={styles.closeIcon} d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
          </svg>
        </button>
      </header>

      <MessageList
        messages={chat.messages}
        intro={chat.empty && !chat.loading}
        error={chat.error}
        onRetry={chat.retry}
        onEditQuestion={editQuestion}
        onOpenSource={onOpenSource}
      />
      {/* Not while loading: a send before the list arrives would start a second conversation. */}
      <Composer
        value={draft}
        onChange={setDraft}
        disabled={chat.sending || chat.loading}
        onSend={send}
        inputRef={inputRef}
      />
    </section>
  );
}
