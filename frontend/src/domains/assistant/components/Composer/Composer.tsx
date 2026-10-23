import { useLayoutEffect, type FormEvent, type KeyboardEvent, type RefObject } from "react";
import styles from "./Composer.module.css";

const MAX_HEIGHT = 120;

type ComposerProps = {
  value: string;
  onChange: (value: string) => void;
  /** Blocks sending (a reply is streaming, or the history is loading); typing stays open. */
  disabled: boolean;
  onSend: (content: string) => void;
  inputRef: RefObject<HTMLTextAreaElement | null>;
};

export function Composer({ value, onChange, disabled, onSend, inputRef }: ComposerProps) {
  const content = value.trim();

  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
  }, [value, inputRef]);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!content || disabled) return;
    onSend(content);
    onChange("");
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) submit(event);
  };

  return (
    <form className={styles.composer} onSubmit={submit}>
      <textarea
        ref={inputRef}
        className={styles.input}
        rows={1}
        placeholder="Ask about your documents…"
        aria-label="Message Quillbert"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={onKeyDown}
      />
      {!value && (
        <kbd className={styles.kbd} aria-hidden>
          ⌘K
        </kbd>
      )}
      <button type="submit" className={styles.send} aria-label="Send" disabled={disabled || !content}>
        ➤
      </button>
    </form>
  );
}
