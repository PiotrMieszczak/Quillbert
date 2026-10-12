import { useEffect, useState } from "react";
import { NAV_ITEMS, TAB_IDS } from "../navItems";
import styles from "./TabBar.module.css";

type TabBarProps = {
  active: string;
  onNavigate: (id: string) => void;
};

const TABS = TAB_IDS.map((id) => NAV_ITEMS.find((item) => item.id === id)!);
const OVERFLOW = NAV_ITEMS.filter((item) => !TAB_IDS.includes(item.id));

export function TabBar({ active, onNavigate }: TabBarProps) {
  const [moreOpen, setMoreOpen] = useState(false);

  // A sheet that survives rotation into desktop width would be stranded,
  // since the bar itself is hidden above 900px.
  useEffect(() => {
    if (!moreOpen) return;
    const close = () => setMoreOpen(false);
    const media = window.matchMedia("(min-width: 901px)");
    media.addEventListener("change", close);
    return () => media.removeEventListener("change", close);
  }, [moreOpen]);

  useEffect(() => {
    if (!moreOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMoreOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [moreOpen]);

  const inOverflow = OVERFLOW.some((item) => item.id === active);

  return (
    <>
      <nav className={styles.bar} aria-label="Workspace">
        {TABS.map((item) => {
          const isActive = item.id === active;
          return (
            <button
              key={item.id}
              type="button"
              className={[styles.tab, isActive && styles.active].filter(Boolean).join(" ")}
              aria-current={isActive ? "page" : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <span className={styles.glyph} aria-hidden>
                {item.glyph}
              </span>
              <span className={styles.label}>{item.short ?? item.label}</span>
            </button>
          );
        })}

        <button
          type="button"
          className={[styles.tab, inOverflow && styles.active].filter(Boolean).join(" ")}
          aria-expanded={moreOpen}
          onClick={() => setMoreOpen((open) => !open)}
        >
          <span className={styles.glyph} aria-hidden>
            ⋯
          </span>
          <span className={styles.label}>More</span>
        </button>
      </nav>

      {moreOpen && (
        <>
          <button
            type="button"
            className={styles.backdrop}
            aria-label="Close menu"
            onClick={() => setMoreOpen(false)}
          />
          <div className={styles.sheet} role="dialog" aria-label="More views">
            <div className={styles.handle} aria-hidden />
            {OVERFLOW.map((item) => (
              <button
                key={item.id}
                type="button"
                className={styles.sheetItem}
                aria-current={item.id === active ? "page" : undefined}
                onClick={() => {
                  setMoreOpen(false);
                  onNavigate(item.id);
                }}
              >
                <span className={styles.glyph} aria-hidden>
                  {item.glyph}
                </span>
                {item.label}
              </button>
            ))}
          </div>
        </>
      )}
    </>
  );
}
