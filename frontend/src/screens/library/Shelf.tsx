import { DocumentLibrary } from "../../domains/library";
import { PageTitle, ThemeToggle } from "../../ui/components";
import styles from "./Shelf.module.css";

type ShelfProps = {
  shelf: "library" | "vault";
  /** Only an admin writes the vault; the server checks too (ADR-0027). */
  admin: boolean;
  onBack: () => void;
};

const COPY = {
  library: {
    title: "My library",
    sub: "Your own references and methods. Every one of your campaigns reads them.",
  },
  vault: {
    title: "Vault",
    sub: "Shared knowledge every Quillbert reads: open rules and reference material.",
  },
};

/** The GM's library, or the vault: documents outside any one campaign. */
export function Shelf({ shelf, admin, onBack }: ShelfProps) {
  const readOnly = shelf === "vault" && !admin;
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button type="button" className={styles.back} onClick={onBack}>
          ← Campaigns
        </button>
        <ThemeToggle />
      </header>
      <main className={styles.main}>
        <PageTitle>{COPY[shelf].title}</PageTitle>
        <p className={styles.sub}>
          {COPY[shelf].sub}
          {readOnly && " Read-only: the admin maintains it."}
        </p>
        <DocumentLibrary source={shelf} readOnly={readOnly} />
      </main>
    </div>
  );
}
