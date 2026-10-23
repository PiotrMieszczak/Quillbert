import { useEffect, useRef } from "react";
import { mountAmbient } from "./ambient";
import styles from "./AmbientCanvas.module.css";

/** The library orrery behind every screen. Decorative: no pointer events, hidden from assistive tech. */
export function AmbientCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => mountAmbient(ref.current!), []);
  return <canvas ref={ref} className={styles.canvas} aria-hidden />;
}
