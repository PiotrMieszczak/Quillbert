import { useState, type ComponentType } from "react";
import { signOut, useAuthStore } from "../domains/auth";
import { CAMPAIGN } from "../domains/campaign";
import { Login } from "../screens/login/Login";
import { Documents } from "../screens/workspace/Documents";
import { Overview } from "../screens/workspace/Overview";
import { WorkspaceShell } from "./shell";

// shortcut: view lives in state, not the URL; React Router replaces this in #7.
const VIEWS: Record<string, ComponentType> = {
  overview: Overview,
  documents: Documents,
};

export function App() {
  const { ready, session, recovering } = useAuthStore();
  const [view, setView] = useState("overview");
  if (!ready) return null;
  // A reset link signs the user in; keep them on the form until they pick a new password.
  if (!session || recovering) return <Login />;
  const View = VIEWS[view] ?? Overview;
  return (
    <WorkspaceShell
      campaign={CAMPAIGN}
      activeView={view}
      onNavigate={(id) => VIEWS[id] && setView(id)}
      onSignOut={() => void signOut()}
    >
      <View />
    </WorkspaceShell>
  );
}
