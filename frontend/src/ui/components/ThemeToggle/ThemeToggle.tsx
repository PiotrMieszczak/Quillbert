import { useState } from "react";
import styles from "./ThemeToggle.module.css";

const KEY = "rf-theme";

/** Flips <html data-theme> between dark and light. index.html applies the saved choice before first paint. */
export function ThemeToggle() {
  const [light, setLight] = useState(() => document.documentElement.dataset.theme === "light");

  const toggle = () => {
    const next = !light;
    setLight(next);
    if (next) document.documentElement.dataset.theme = "light";
    else delete document.documentElement.dataset.theme;
    try {
      localStorage.setItem(KEY, next ? "light" : "dark");
    } catch {
      // Storage blocked: the theme still applies for this visit.
    }
  };

  return (
    <button
      type="button"
      className={styles.toggle}
      onClick={toggle}
      aria-label={light ? "Switch to dark theme" : "Switch to light theme"}
      title="Toggle light / dark"
    >
      {light ? (
        <svg width="17" height="17" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
          <path d="M15.2 11.2A6.5 6.5 0 0 1 6.8 2.8a6.5 6.5 0 1 0 8.4 8.4z" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="17" height="17" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
          <circle cx="9" cy="9" r="3.4" />
          <path
            d="M9 1.8v1.8M9 14.4v1.8M1.8 9h1.8M14.4 9h1.8M3.9 3.9l1.3 1.3M12.8 12.8l1.3 1.3M3.9 14.1l1.3-1.3M12.8 5.2l1.3-1.3"
            strokeLinecap="round"
          />
        </svg>
      )}
    </button>
  );
}
