import { useState } from "react";
import { resendConfirmation } from "../../api";
import styles from "./LoginForm.module.css";

type Props = { email: string; onBack: () => void; onChangeAddress: () => void };
type Message = { kind: "error" | "notice"; text: string };

/** Shown after sign-up when the project requires the address to be confirmed. */
export function CheckEmail({ email, onBack, onChangeAddress }: Props) {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);

  async function resend() {
    setPending(true);
    setMessage(null);
    try {
      await resendConfirmation(email);
      setMessage({ kind: "notice", text: "Sent again. Check your spam folder too." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Something went wrong." });
    } finally {
      setPending(false);
    }
  }

  return (
    <div className={styles.card}>
      <div className={styles.sentIcon} aria-hidden="true">
        <MailGlyph />
      </div>
      <h1 className={`${styles.title} ${styles.centered}`}>Check your email</h1>
      <p className={`${styles.subtitle} ${styles.centered}`}>
        We sent a confirmation link to <strong className={styles.address}>{email}</strong>. Open it to finish creating your
        account.
      </p>

      {message && (
        <p
          className={`${message.kind === "error" ? styles.error : styles.notice} ${styles.centered}`}
          role={message.kind === "error" ? "alert" : "status"}
        >
          {message.text}
        </p>
      )}

      <button type="button" className={styles.secondary} disabled={pending} onClick={() => void resend()}>
        Resend email
      </button>

      <p className={styles.footer}>
        Wrong address?{" "}
        <button type="button" className={styles.link} onClick={onChangeAddress}>
          Start over
        </button>
        {" · "}
        <button type="button" className={styles.link} onClick={onBack}>
          Back to sign in
        </button>
      </p>
    </div>
  );
}

function MailGlyph() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="5" width="18" height="14" rx="2.5" />
      <path d="m4 7 8 6 8-6" />
    </svg>
  );
}
