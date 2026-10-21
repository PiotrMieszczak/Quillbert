import { useEffect } from "react";
import type { Campaign } from "../../../campaign";
import { useChat } from "../../api/useChat";
import { Composer } from "../Composer";
import { MessageList } from "../MessageList";
import styles from "./AssistantPanel.module.css";

type AssistantPanelProps = {
  campaign: Campaign;
  open: boolean;
  onClose: () => void;
};

export function AssistantPanel({ campaign, open, onClose }: AssistantPanelProps) {
  const chat = useChat(campaign.id);
  const { abort } = chat;

  // The panel stays mounted when closed; closing stops the reply in flight.
  useEffect(() => {
    if (!open) abort();
  }, [open, abort]);

  return (
    <section className={styles.panel} aria-label="Quillbert">
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
          className={styles.reset}
          aria-label="New conversation"
          title="New conversation"
          disabled={!chat.canReset}
          onClick={chat.newConversation}
        >
          ✎
        </button>
        <button type="button" className={styles.close} aria-label="Close Quillbert" onClick={onClose}>
          ×
        </button>
      </header>

      <MessageList
        messages={chat.messages}
        intro={chat.empty && !chat.loading}
        error={chat.error}
        onRetry={chat.retry}
      />
      <Composer disabled={chat.sending} onSend={chat.send} />
    </section>
  );
}
