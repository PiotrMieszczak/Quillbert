import { useState, type ComponentType } from "react";
import { CAMPAIGN } from "../domains/campaign";
import { Documents } from "../screens/workspace/Documents";
import { Overview } from "../screens/workspace/Overview";
import { WorkspaceShell } from "./shell";

// shortcut: view lives in state, not the URL; React Router replaces this in #7.
const VIEWS: Record<string, ComponentType> = {
  overview: Overview,
  documents: Documents,
};

export function App() {
  const [view, setView] = useState("overview");
  const View = VIEWS[view] ?? Overview;
  return (
    <WorkspaceShell
      campaign={CAMPAIGN}
      activeView={view}
      onNavigate={(id) => VIEWS[id] && setView(id)}
    >
      <View />
    </WorkspaceShell>
  );
}
