import { LoginForm } from "../../domains/auth";
import styles from "./Login.module.css";

export function Login() {
  return (
    <main className={styles.page}>
      <div className={styles.brand}>
        <div className={styles.tile} aria-hidden="true">
          ✦
        </div>
        <div className={styles.name}>Referee</div>
        <div className={styles.tagline}>ASSISTANT</div>
      </div>
      <LoginForm />
    </main>
  );
}
