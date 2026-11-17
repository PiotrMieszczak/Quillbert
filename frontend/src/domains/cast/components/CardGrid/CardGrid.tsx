import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ApiError } from "../../../../lib/api";
import styles from "./CardGrid.module.css";

type CardGridProps<T extends { id: string }> = {
  query: UseQueryResult<T[]>;
  /** Shown in place of the grid when the list is empty. */
  empty: string;
  children: (item: T) => ReactNode;
};

/** The card grid of a cast query, with its loading, load-error and empty states in place of the
 *  grid, as on Documents (docs/design/overview.md §4). */
export function CardGrid<T extends { id: string }>({ query, empty, children }: CardGridProps<T>) {
  if (query.isPending) return <p className={styles.message}>Loading…</p>;
  if (query.isError)
    return (
      <p className={styles.message} role="alert">
        Could not load. {query.error instanceof ApiError ? query.error.message : "Check your connection."}{" "}
        <button type="button" className={styles.retry} onClick={() => void query.refetch()}>
          Try again
        </button>
      </p>
    );
  if (query.data.length === 0) return <p className={styles.message}>{empty}</p>;
  return (
    <ul className={styles.grid}>
      {query.data.map((item) => (
        <li key={item.id}>{children(item)}</li>
      ))}
    </ul>
  );
}
