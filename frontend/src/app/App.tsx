import { useState, type ComponentType } from "react";
import { signOut, useAuthStore } from "../domains/auth";
import type { Campaign } from "../domains/campaign";
import { CampaignPicker } from "../screens/campaigns/CampaignPicker";
import { Login } from "../screens/login/Login";
import { Documents } from "../screens/workspace/Documents";
import { WorkspaceShell } from "./shell";

// shortcut: view and campaign live in state, not the URL; React Router replaces this in #7.
// Overview is unlisted while it shows fixture data; see navItems `built`.
const VIEWS: Record<string, ComponentType<{ campaign: Campaign }>> = {
  documents: Documents,
};

export function App() {
  const { ready, session, recovering } = useAuthStore();
  const [view, setView] = useState("documents");
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  if (!ready) return null;
  // A reset link signs the user in; keep them on the form until they pick a new password.
  if (!session || recovering) return <Login />;

  const leave = () => {
    setCampaign(null);
    void signOut();
  };
  if (!campaign) {
    return <CampaignPicker email={session.user.email} onOpen={setCampaign} onSignOut={leave} />;
  }

  const View = VIEWS[view] ?? Documents;
  return (
    <WorkspaceShell
      campaign={campaign}
      activeView={view}
      onNavigate={(id) => VIEWS[id] && setView(id)}
      onSwitchCampaign={() => setCampaign(null)}
      onSignOut={leave}
    >
      <View campaign={campaign} />
    </WorkspaceShell>
  );
}
