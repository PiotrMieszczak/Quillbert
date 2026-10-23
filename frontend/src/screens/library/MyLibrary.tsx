import { DocumentLibrary } from "../../domains/library";
import { PageTitle, ThemeToggle } from "../../ui/components";
import styles from "./MyLibrary.module.css";

/** The GM's own library, outside any one campaign: every campaign of theirs reads it (ADR-0027). */
export function MyLibrary({ onBack }: { onBack: () => void }) {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button type="button" className={styles.back} onClick={onBack}>
          ← Campaigns
        </button>
        <ThemeToggle />
      </header>
      <main className={styles.main}>
        <PageTitle>My library</PageTitle>
        <p className={styles.sub}>Your own references and methods. Every one of your campaigns reads them.</p>
        <DocumentLibrary source="library" />
      </main>
    </div>
  );
}
