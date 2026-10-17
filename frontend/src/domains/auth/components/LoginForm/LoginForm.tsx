import { useState, type FormEvent } from "react";
import {
  requestPasswordReset,
  setNewPassword,
  signIn,
  signInWithGoogle,
  signUp,
} from "../../api";
import { useAuthStore } from "../../store";
import { CheckEmail } from "./CheckEmail";
import styles from "./LoginForm.module.css";

type Mode = "signin" | "signup" | "forgot" | "recovery" | "confirm";
type Message = { kind: "error" | "notice"; text: string };

const TITLES: Record<Exclude<Mode, "confirm">, [string, string]> = {
  signin: ["Sign in", "Continue to your table"],
  signup: ["Create your account", "One account per game master"],
  forgot: ["Reset password", "We'll email you a link"],
  recovery: ["New password", "Choose one to finish the reset"],
};

// Same text whether or not the address exists (AC-011): no account enumeration.
const RESET_SENT = "If that address has an account, a reset link has been sent.";

export function LoginForm() {
  const recovering = useAuthStore((state) => state.recovering);
  const [chosen, setMode] = useState<Mode>("signin");
  const mode = recovering ? "recovery" : chosen;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<Message | null>(null);
  const [pending, setPending] = useState(false);

  const go = (next: Mode) => {
    setMode(next);
    setMessage(null);
  };

  // Sign-up with email confirmation on: a screen of its own, not a line under the form.
  if (mode === "confirm") {
    return <CheckEmail email={email} onBack={() => go("signin")} onChangeAddress={() => go("signup")} />;
  }
  const [title, subtitle] = TITLES[mode];

  async function run(action: () => Promise<Message | null | void>) {
    setPending(true);
    setMessage(null);
    try {
      setMessage((await action()) ?? null);
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "Something went wrong." });
    } finally {
      setPending(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (mode === "signin") return void (await signIn(email, password));
      if (mode === "signup") {
        if (!(await signUp(email, password))) {
          setPassword("");
          setMode("confirm");
        }
        return null;
      }
      if (mode === "forgot") {
        await requestPasswordReset(email);
        return { kind: "notice", text: RESET_SENT };
      }
      await setNewPassword(password);
    });
  }

  const needsEmail = mode !== "recovery";
  const needsPassword = mode !== "forgot";

  return (
    <div className={styles.card}>
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.subtitle}>{subtitle}</p>

      <form className={styles.form} onSubmit={submit}>
        {needsEmail && (
          <label className={styles.field}>
            <span className={styles.label}>Email</span>
            <input
              className={styles.input}
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
        )}
        {needsPassword && (
          <label className={styles.field}>
            <span className={styles.labelRow}>
              <span className={styles.label}>{mode === "recovery" ? "New password" : "Password"}</span>
              {mode === "signin" && (
                <button type="button" className={styles.link} onClick={() => go("forgot")}>
                  Forgot?
                </button>
              )}
            </span>
            <input
              className={styles.input}
              type="password"
              autoComplete={mode === "signin" ? "current-password" : "new-password"}
              minLength={mode === "signin" ? undefined : 8}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
        )}

        {message && (
          <p className={message.kind === "error" ? styles.error : styles.notice} role={message.kind === "error" ? "alert" : "status"}>
            {message.text}
          </p>
        )}

        <button type="submit" className={styles.primary} disabled={pending}>
          {{ signin: "Sign in", signup: "Create account", forgot: "Send reset link", recovery: "Set password" }[mode]}
        </button>
      </form>

      {(mode === "signin" || mode === "signup") && (
        <>
          <div className={styles.divider}>OR</div>
          <button type="button" className={styles.google} disabled={pending} onClick={() => void run(signInWithGoogle)}>
            <GoogleGlyph />
            Continue with Google
          </button>
        </>
      )}

      <p className={styles.footer}>
        {mode === "signin" && (
          <>
            New to Quillbert?{" "}
            <button type="button" className={styles.link} onClick={() => go("signup")}>
              Create account
            </button>
          </>
        )}
        {mode === "signup" && (
          <>
            Already have an account?{" "}
            <button type="button" className={styles.link} onClick={() => go("signin")}>
              Sign in
            </button>
          </>
        )}
        {mode === "forgot" && (
          <button type="button" className={styles.link} onClick={() => go("signin")}>
            Back to sign in
          </button>
        )}
      </p>
    </div>
  );
}

function GoogleGlyph() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#4285F4" d="M45.1 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h11.8c-.5 2.7-2.1 5-4.4 6.5v5.4h7.1c4.2-3.8 6.6-9.5 6.6-15.9z" />
      <path fill="#34A853" d="M24 46c6 0 11.1-2 14.5-5.4l-7.1-5.4c-2 1.3-4.5 2.1-7.4 2.1-5.7 0-10.5-3.8-12.2-9H4.5v5.6C7.9 40.8 15.4 46 24 46z" />
      <path fill="#FBBC05" d="M11.8 28.3c-.4-1.3-.7-2.7-.7-4.3s.3-2.9.7-4.3v-5.6H4.5C3 17 2 20.4 2 24s1 7 2.5 9.9l7.3-5.6z" />
      <path fill="#EA4335" d="M24 10.7c3.2 0 6.1 1.1 8.4 3.3l6.3-6.3C35.1 4.2 30 2 24 2 15.4 2 7.9 7.2 4.5 14.1l7.3 5.6c1.7-5.2 6.5-9 12.2-9z" />
    </svg>
  );
}
