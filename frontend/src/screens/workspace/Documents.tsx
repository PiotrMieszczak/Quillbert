import { DocumentLibrary } from "../../domains/library";
import { PageTitle } from "../../ui/components";
import styles from "./Documents.module.css";

export function Documents() {
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <PageTitle>Document Library</PageTitle>
        <p className={styles.sub}>
          Deterministic extraction · text, stat blocks, and rules indexed for search
        </p>
      </header>
      <DocumentLibrary />
    </div>
  );
}
