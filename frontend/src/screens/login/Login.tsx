import { LoginForm } from "../../domains/auth";
import styles from "./Login.module.css";

export function Login() {
  return (
    <main className={styles.page}>
      <div className={styles.brand}>
        <div className={styles.tile} aria-hidden="true">
          <img className={styles.mark} src="/quillbert-mark.svg" alt="" />
        </div>
        <div className={styles.name}>Quillbert</div>
        <div className={styles.tagline}>YOUR TTRPG ASSISTANT</div>
      </div>
      <LoginForm />
    </main>
  );
}
