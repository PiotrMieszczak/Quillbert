import { Fragment, useState } from "react";
import type { Message } from "../../model/types";
import { ThinkingIndicator } from "../ThinkingIndicator";
import { useWordReveal } from "./useWordReveal";
import styles from "./MessageBubble.module.css";

type MessageBubbleProps = {
  message: Message;
  /** Opens a cited document in the library. */
  onOpenSource: (documentId: string) => void;
  /** A refused reply's "Add documents": shows the upload zone. */
  onAddDocuments: () => void;
};

const CITATION = /\[S(\d+)\]/g;
const WORDS = /\S+\s*/g;
const COPIED_MS = 1600;

/** `[S2]` in the reply becomes a superscript 2, matching the "2" on its source chip. */
function withCitations(content: string) {
  return content.split(CITATION).map((part, index) =>
    index % 2 === 1 ? (
      <sup key={index} className={styles.cite}>
        <span className={styles.srOnly}>source </span>
        {part}
      </sup>
    ) : (
      <Fragment key={index}>{part}</Fragment>
    ),
  );
}

export function MessageBubble({ message, onOpenSource, onAddDocuments }: MessageBubbleProps) {
  if (message.role === "user") {
    return (
      <article className={[styles.userRow, message.phase && styles.arrive].filter(Boolean).join(" ")}>
        <div className={styles.user}>{message.content}</div>
      </article>
    );
  }
  return <Reply message={message} onOpenSource={onOpenSource} onAddDocuments={onAddDocuments} />;
}

function Reply({ message, onOpenSource, onAddDocuments }: MessageBubbleProps) {
  const live = message.phase !== undefined;
  const streaming = message.phase === "waiting" || message.phase === "streaming";
  const words = message.content.match(WORDS) ?? [];
  // While streaming, hold back the last word: it may still be arriving.
  const ready = streaming ? Math.max(0, words.length - 1) : words.length;
  const shown = useWordReveal(ready, live);
  const writing = streaming || shown < words.length;

  if (streaming && words.length === 0) {
    return <ThinkingIndicator searched={message.searched} />;
  }

  return (
    <article className={[styles.reply, (live || message.id === "intro") && styles.arrive].filter(Boolean).join(" ")}>
      <div className={styles.name}>
        <img className={writing ? styles.bob : undefined} src="/quillbert-mark.svg" alt="" />
        Quillbert
      </div>
      <p className={styles.body}>
        {live
          ? words.slice(0, shown).map((word, index) => (
              <span key={index} className={styles.ink}>
                {withCitations(word)}
              </span>
            ))
          : withCitations(message.content)}
        {writing && <span className={styles.cursor} aria-hidden />}
      </p>
      {!writing && message.citations.length > 0 && (
        <ul className={styles.sources} aria-label="Sources">
          {message.citations.map((citation, index) => (
            <li key={citation.label}>
              <button
                type="button"
                className={styles.source}
                style={live ? { animationDelay: `${index * 0.12}s` } : { animation: "none" }}
                title={[!citation.attribution && "Open in Documents", citation.heading, citation.attribution]
                  .filter(Boolean)
                  .join(" · ")}
                // A library passage is not in this campaign's Documents (ADR-0027).
                // Not `disabled`: the tooltip carries the layer and must still show.
                aria-disabled={citation.attribution !== null}
                onClick={() => citation.attribution === null && onOpenSource(citation.documentId)}
              >
                <span className={styles.sourceN}>{citation.label.slice(1)}</span>
                {citation.filename}
                {citation.page && <span className={styles.sourcePage}>p. {citation.page}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
      {!writing && message.refused && (
        <div className={styles.refusal}>
          {message.searched && <p className={styles.searched}>{message.searched}</p>}
          <p className={styles.hint}>Try the name your notes use for it, or add the book or notes that cover it.</p>
          <button type="button" className={styles.addDocuments} onClick={onAddDocuments}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
              <path d="M12 16V4m0 0L8 8m4-4l4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Add documents
          </button>
        </div>
      )}
      {!writing && message.id !== "intro" && <CopyButton text={message.content} />}
    </article>
  );
}

function CopyButton({ text }: { text: string }) {
  const [result, setResult] = useState<"copied" | "failed" | null>(null);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setResult("copied");
    } catch {
      setResult("failed"); // Clipboard blocked by the browser or a permission policy.
    }
    setTimeout(() => setResult(null), COPIED_MS);
  };

  return (
    <div className={styles.actions}>
      <button type="button" className={[styles.action, result && styles[result]].filter(Boolean).join(" ")} onClick={copy}>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d={result === "copied" ? "M2.5 7.2l3 3L11.5 4" : "M4.5 4.5V2.5h7v7h-2M2.5 4.5h7v7h-7z"} />
        </svg>
        <span aria-live="polite">{result === "copied" ? "Copied" : result === "failed" ? "Couldn’t copy" : "Copy"}</span>
      </button>
    </div>
  );
}
