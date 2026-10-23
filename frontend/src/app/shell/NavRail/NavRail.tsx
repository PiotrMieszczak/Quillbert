import { NavIcon } from "../NavIcon";
import { NAV_ITEMS } from "../navItems";
import styles from "./NavRail.module.css";

type NavRailProps = {
  active: string;
  onNavigate: (id: string) => void;
};

export function NavRail({ active, onNavigate }: NavRailProps) {
  return (
    <nav className={styles.rail} aria-label="Workspace">
      <div className={styles.brand}>
        <span className={styles.mark}>
          <img src="/quillbert-mark.svg" alt="" />
        </span>
        <span className={styles.brandName}>Quillbert</span>
      </div>
      {NAV_ITEMS.map((item) => {
        const isActive = item.id === active;
        return (
          <button
            key={item.id}
            type="button"
            title={item.label}
            className={[styles.item, isActive && styles.active].filter(Boolean).join(" ")}
            aria-current={isActive ? "page" : undefined}
            onClick={() => onNavigate(item.id)}
          >
            <span className={styles.glyph}>
              <NavIcon id={item.id} />
            </span>
            <span className={styles.label}>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
