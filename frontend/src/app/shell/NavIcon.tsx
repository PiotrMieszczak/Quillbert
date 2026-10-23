import type { ReactNode } from "react";

/** Stroke icons for the rail and tab bar, transcribed from the design prototype (BND-004). */
const PATHS: Record<string, ReactNode> = {
  overview: (
    <g>
      <rect x={3} y={3} width={6} height={6} rx={1.5} />
      <rect x={11} y={3} width={6} height={6} rx={1.5} />
      <rect x={3} y={11} width={6} height={6} rx={1.5} />
      <rect x={11} y={11} width={6} height={6} rx={1.5} />
    </g>
  ),
  npcs: (
    <g strokeLinecap="round" strokeLinejoin="round">
      <circle cx={10} cy={7} r={3} />
      <path d="M4 17c0-3.3 2.7-5 6-5s6 1.7 6 5" />
    </g>
  ),
  players: (
    <g strokeLinecap="round" strokeLinejoin="round">
      <circle cx={7} cy={6} r={2.6} />
      <circle cx={14} cy={7} r={2.2} />
      <path d="M2.5 16c0-2.6 2-4.2 4.5-4.2s4.5 1.6 4.5 4.2" />
      <path d="M12.5 12c2.2 0 4 1.5 4 4" />
    </g>
  ),
  factions: (
    <g strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 17V4l7 1.5L18 4v9l-6 1.5L5 13" />
      <path d="M5 4v13" />
    </g>
  ),
  quests: (
    <g strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 3h7l3 3v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M7 9l1.6 1.6L12 7" />
    </g>
  ),
  documents: (
    <g strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 3h6l4 4v10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M11 3v4h4M7 11h6M7 14h6" />
    </g>
  ),
  graph: (
    <g strokeLinecap="round">
      <circle cx={5} cy={6} r={2} />
      <circle cx={15} cy={5} r={2} />
      <circle cx={10} cy={15} r={2} />
      <path d="M6.6 7.2L9 13m1.8-.2L14 6.5M6.8 5.6L13.2 5" />
    </g>
  ),
  sessions: (
    <g strokeLinecap="round" strokeLinejoin="round">
      <circle cx={10} cy={10} r={7} />
      <path d="M10 6v4l3 2" />
    </g>
  ),
  more: (
    <g fill="currentColor" stroke="none">
      <circle cx={4} cy={10} r={1.7} />
      <circle cx={10} cy={10} r={1.7} />
      <circle cx={16} cy={10} r={1.7} />
    </g>
  ),
};

export function NavIcon({ id }: { id: string }) {
  return (
    <svg width={18} height={18} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} aria-hidden>
      {PATHS[id]}
    </svg>
  );
}
