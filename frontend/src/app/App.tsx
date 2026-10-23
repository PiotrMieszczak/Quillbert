import { useState, type ComponentType } from "react";
import { signOut, useAuthStore } from "../domains/auth";
import type { Campaign } from "../domains/campaign";
import { CampaignPicker } from "../screens/campaigns/CampaignPicker";
import { MyLibrary } from "../screens/library/MyLibrary";
import { Login } from "../screens/login/Login";
import { Documents, type DocumentFocus } from "../screens/workspace/Documents";
import { AmbientCanvas } from "./ambient";
import { WorkspaceShell } from "./shell";

// shortcut: view and campaign live in state, not the URL; React Router replaces this in #7.
// Overview is unlisted while it shows fixture data; see navItems `built`.
const VIEWS: Record<string, ComponentType<{ campaign: Campaign; focus: DocumentFocus | null }>> = {
  documents: Documents,
};

export function App() {
  return (
    <>
      <AmbientCanvas />
      <Screen />
    </>
  );
}

function Screen() {
  const { ready, session, recovering } = useAuthStore();
  const [view, setView] = useState("documents");
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [library, setLibrary] = useState(false);
  // The document a citation chip asked to see; `at` re-triggers the highlight on a repeat click.
  const [focus, setFocus] = useState<DocumentFocus | null>(null);
  if (!ready) return null;
  // A reset link signs the user in; keep them on the form until they pick a new password.
  if (!session || recovering) return <Login />;

  const leave = () => {
    setCampaign(null);
    setLibrary(false);
    void signOut();
  };
  if (library) return <MyLibrary onBack={() => setLibrary(false)} />;
  if (!campaign) {
    return (
      <CampaignPicker email={session.user.email} onOpen={setCampaign} onOpenLibrary={() => setLibrary(true)} onSignOut={leave} />
    );
  }

  const View = VIEWS[view] ?? Documents;
  return (
    <WorkspaceShell
      campaign={campaign}
      activeView={view}
      onNavigate={(id) => VIEWS[id] && setView(id)}
      onSwitchCampaign={() => setCampaign(null)}
      onSignOut={leave}
      onOpenSource={(documentId) => {
        setView("documents");
        setFocus({ documentId, at: Date.now() });
      }}
    >
      <View campaign={campaign} focus={focus} />
    </WorkspaceShell>
  );
}
