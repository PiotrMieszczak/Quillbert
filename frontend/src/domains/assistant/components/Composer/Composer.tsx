import { useLayoutEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import styles from "./Composer.module.css";

const MAX_HEIGHT = 120;

type ComposerProps = {
  /** True while a reply streams. */
  disabled: boolean;
  onSend: (content: string) => void;
};

export function Composer({ disabled, onSend }: ComposerProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [value, setValue] = useState("");
  const content = value.trim();

  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
  }, [value]);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!content || disabled) return;
    onSend(content);
    setValue("");
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
        disabled={disabled}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={onKeyDown}
      />
      <button type="submit" className={styles.send} aria-label="Send" disabled={disabled || !content}>
        ➤
      </button>
    </form>
  );
}
