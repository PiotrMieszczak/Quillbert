import { Fragment } from "react";
import type { Message } from "../../model/types";
import { ToolChip } from "../ToolChip";
import styles from "./MessageBubble.module.css";

type MessageBubbleProps = {
  message: Message;
};

const CITATION = /\[S(\d+)\]/g;

/** `[S2]` in the reply becomes a superscript 2; the numbered source list sits under the bubble. */
function withCitations(content: string) {
  return content.split(CITATION).map((part, index) =>
    index % 2 === 1 ? <sup key={index} className={styles.cite}>{part}</sup> : <Fragment key={index}>{part}</Fragment>,
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  return (
    <article className={[styles.row, isUser ? styles.userRow : styles.assistantRow].join(" ")}>
      <div className={styles.stack}>
        <div className={[styles.bubble, isUser ? styles.user : styles.assistant].join(" ")}>
          {message.searched && <ToolChip label={message.searched} />}
          {message.phase === "waiting" ? (
            <span className={styles.dots} role="status" aria-label="Quillbert is thinking">
              <span />
              <span />
              <span />
            </span>
          ) : (
            <p className={styles.body}>
              {withCitations(message.content)}
              {message.phase === "streaming" && <span className={styles.cursor} aria-hidden />}
            </p>
          )}
        </div>
        {message.citations.length > 0 && (
          <ol className={styles.sources}>
            {message.citations.map((citation) => (
              <li key={citation.label} value={Number(citation.label.slice(1))}>
                {[citation.filename, citation.page && `p.${citation.page}`, citation.heading, citation.attribution]
                  .filter(Boolean)
                  .join(" · ")}
              </li>
            ))}
          </ol>
        )}
      </div>
    </article>
  );
}
