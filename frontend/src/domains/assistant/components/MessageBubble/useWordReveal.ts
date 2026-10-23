import { useEffect, useState } from "react";

const STEP_MS = 42;
/** Beyond this backlog the reveal shows more than one word per step, so it never falls far behind. */
const CATCH_UP_WORDS = 40;
const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** How many of `ready` words to show. Animated replies reveal a steady word per step, so bursty
 *  streams still flow, speeding up only when far behind; history and reduced motion show it all. */
export function useWordReveal(ready: number, animate: boolean) {
  const [shown, setShown] = useState(0);
  const pacing = animate && shown < ready && !reducedMotion();

  useEffect(() => {
    if (!pacing) return;
    const step = setTimeout(
      () => setShown((n) => n + Math.max(1, Math.ceil((ready - n) / CATCH_UP_WORDS))),
      STEP_MS,
    );
    return () => clearTimeout(step);
  }, [pacing, shown, ready]);

  return pacing ? shown : ready;
}
