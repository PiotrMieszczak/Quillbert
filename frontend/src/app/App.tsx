import { useState, type ComponentType } from "react";
import { signOut, useAuthStore } from "../domains/auth";
import { CAMPAIGN } from "../domains/campaign";
import { Login } from "../screens/login/Login";
import { Documents } from "../screens/workspace/Documents";
import { WorkspaceShell } from "./shell";

// shortcut: view lives in state, not the URL; React Router replaces this in #7.
// Overview is unlisted while it shows fixture data; see navItems `built`.
const VIEWS: Record<string, ComponentType> = {
  documents: Documents,
};

export function App() {
  const { ready, session, recovering } = useAuthStore();
  const [view, setView] = useState("documents");
  if (!ready) return null;
  // A reset link signs the user in; keep them on the form until they pick a new password.
  if (!session || recovering) return <Login />;
  const View = VIEWS[view] ?? Documents;
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
