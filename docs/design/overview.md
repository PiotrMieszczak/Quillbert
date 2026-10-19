# Design

Screens, layout, and behaviour. Exact values live in [reference.md](reference.md).

## The prototype

**▶ [Open the interactive design](https://claude.ai/code/artifact/a7d4de30-0826-4747-b295-a584fe6f0f28)**

This is the source of truth. It is the running prototype, not a picture of one — click
through the login and campaign picker into the workspace, switch views from the nav rail,
hover a graph node, toggle the assistant panel, and resize below 900px to see the mobile
shell.

Prefer it over any screenshot. A screenshot captures one frame of one state and goes stale
silently; the prototype shows current behaviour, and interaction is most of what this
design specifies.

Two things to know about the link:

- It is **pinned to a published version**. Republishing the design does not change what
  this link shows until the share pin is moved — deliberate, so the documented design
  cannot shift underfoot mid-implementation.
- Fidelity is **high**. Colors, type, spacing, and interaction states are final as shown.

**Do not port the prototype's code.** It is a `.dc.html` reference with an inline runtime;
read it for structure, layout, and exact values only, and rebuild with the project's own
primitives (BND-004). Its values are transcribed into [reference.md](reference.md), which
is what implementation should follow.

Source project: Claude Design `ec1d38ec-c81f-42b8-8952-7a922851f405`, file
`Referee Workspace.dc.html`.

## Screen model

Two levels of routing. A top-level `screen`, and within the workspace, a `view`.

```mermaid
stateDiagram-v2
    [*] --> Login
    Login --> CampaignPicker: sign in / Google / create account
    CampaignPicker --> Login: sign out
    CampaignPicker --> Workspace: select campaign
    Workspace --> CampaignPicker: switch campaign

    state Workspace {
        [*] --> Overview
        Overview --> NPCs
        NPCs --> CharacterDetail
        Overview --> Players
        Players --> AddPlayer
        Overview --> Factions
        Factions --> FactionDetail
        Overview --> Quests
        Overview --> Documents
        Overview --> Graph
        Graph --> CharacterDetail: click node
        Overview --> Sessions
        Overview --> Settings: avatar
    }
```

Routes map to URLs: `/login`, `/campaigns`, `/c/:campaignId/:view`.

## 1. Login

Full-viewport, vertically centred card on the login radial gradient.

- Card `max-width: 400px`, `--surface-raised`, `1px --border-subtle`,
  `--radius-panel`, `--shadow-card`, padding `26px 24px 24px`
- Brand lockup above the card: 84×84 tile, `--radius-brand`, gradient fill, the gold Quillbert mark
  (`frontend/public/quillbert-mark.svg`, 60px wide);
  "Quillbert" 27px/600 Crimson Pro over "YOUR TTRPG ASSISTANT" 11px, `letter-spacing .14em`, muted
- "Sign in" heading 20px Crimson Pro; subtitle "Continue to your table"
- Email and password inputs: 44px, `--radius-button`, `--surface-sunken`,
  `1px --border-default`; focus border `--accent`
- "Forgot?" link right-aligned above the password field
- Primary button: 46px, `--accent` background, `#0A0C0F` text, `--shadow-accent`,
  hover `brightness(1.06)`
- OR divider — hairline with centred "OR"
- Google button: 44px, `--surface-elevated`, `1px --border-emphasis`, four-color G glyph,
  hover border `--border-emphasis` → `#5A6270`
- Footer: "New to Quillbert? Create account"

**Behaviour.** Real authentication through Supabase Auth
([ADR-0020](../adr/adr-0020-supabase-auth.md)). Sign in and Google advance to the app;
"Create account" switches the card to sign-up; when the project requires email confirmation,
submitting it replaces the card with a **Check your email** screen (envelope tile, the
address it was sent to, **Resend email**, and "Start over" / "Back to sign in") instead of
an inline message; "Forgot?" switches it to a reset request that
shows the same confirmation whether or not the address exists (AC-011). Following a reset
link shows a "New password" card until one is chosen. Until the campaign picker lands, a
session goes straight to the workspace. The same screen serves local and
hosted deployment (PRIN-004).

## 2. Campaign Picker

Full-viewport scroll on the landing radial gradient.

- Header row: brand lockup left; right cluster is "Sign out" plus a 40px avatar
  (`--radius-button`) that opens Settings
- Responsive grid of campaign cards: banner (uploaded image or tint gradient), title in
  Crimson Pro, system badge ("D&D 2024", "Traveller 2e"), meta line
  `Session {n} · {system}`
- An "Add campaign" affordance opens the add-campaign modal

**Add-campaign modal.** Image upload plus a **mandatory** system choice. Create is
disabled until both a name and a system are set. On create, the campaign is added and the
app enters the workspace at Overview.

## 3. Workspace shell

Desktop grid: columns `76px minmax(0,1fr) <panel>` where panel is `400px` open or `0`
closed; rows `--header-height` then content. `height:100vh; width:100vw`.

### Header

Spans all columns. `--surface-app`, bottom border `1px --border-subtle`,
`padding: 0 20px 0 100px`. Shows active campaign name and
`Session {n} · {system}`. Right side: avatar → Settings.

### Floating nav rail

`position: fixed; left: 24px; top: 50%; translateY(-50%)`. Collapsed 60px, icon-only;
expands to 236px on hover **or** when pinned. `--surface-raised`,
`1px --border-strong`, `--radius-rail`, shadow swaps with state.

Items, in order: Overview, NPCs, Players, Factions, Quest Log, Documents,
Knowledge Graph, Sessions. Active item uses `--accent`; labels fade in only when expanded.
Until a destination's view is built it is hidden from the rail and the tab bar, never shown
leading to placeholder content (`built` in `frontend/src/app/shell/navItems.ts`). The tab
bar fills its four tabs from Home, NPCs, Party, Quests first, then any other built view, and
shows **More** only when something is left over.

### AI panel

Right column, `--surface-sunken`, left border `1px --border-subtle`.

- Header: 34px spark tile, "Assistant" over "Grounded in indexed material", a mode pill
  (mono, green dot, current mode — [ADR-0012](../adr/adr-0012-two-ai-modes.md) IMP-005),
  and a close button. There is no provider pill — the provider is not a user choice
  ([ADR-0019](../adr/adr-0019-openrouter-privacy-routing.md))
- Message list: assistant bubbles `--surface-raised` with `14px 14px 14px 4px` radius;
  user bubbles mirrored. Tool-call chips render above content as a green check row in
  mono at 11.5px
- Streaming: a 7×15px accent block with `blink` animation trails the streaming message
- Typing indicator: three dots with staggered `dotpulse`
- Composer: attach button, auto-growing textarea (`max-height: 120px`,
  placeholder "Ask, search, or draft a scene…"), send button. Quick-prompt chips sit
  above the composer when the conversation is short
- Auto-scrolls to the newest message

When closed on desktop, a pill FAB ("✦ Assistant") appears bottom-right.

## 4. Workspace views

| View | Content |
|------|---------|
| **Overview** | Hero block plus a 4-up stat grid and a recent-activity list |
| **NPCs** | Relationship filter chips (All / Allies / Enemies / Family / Pro / Neutral) over a card grid. Cards show portrait, name, role, level, location, tags, and a relationship-coloured accent |
| **Players** | Party cards showing character and player name, class, level; "Add Player" opens a form view |
| **Factions** | Cards with name, type, influence, motto, member count, relationship colour |
| **Quests** | Status tabs (Available / In progress / Completed / Failed / Inactive) over rows with gradient glyph tile, title, subquest line, progress bar, and actions. Failed and inactive quests offer Reactivate |
| **Documents** | List with type badge, page count, meta line, status pill (`Indexed` green / `Processing` accent / `Queued` muted / `Failed` red) and a progress bar. Files upload as soon as they are dropped or picked: each shows an `Uploading` row until the API accepts it, then the real `Queued` row; an `Uploading` row has **Cancel**, which aborts the request and drops the row;
a refused file stays as a red `Failed` row with the server's reason and a dismiss button;
a stored document has a remove (trash) button that turns into **Remove** / **Keep** before
anything is deleted; bytes the campaign already has show "already in the library as …" and add no row. The list polls while anything is queued or processing. Loading, load-error (with *Try again*) and empty states sit where the list goes |
| **Knowledge Graph** | Interactive node graph with relationship legend and search |
| **Sessions** | Date-tile entries with title, duration, tags, and summary; a rich-text composer creates new entries |
| **Settings** | Reached via avatar, not the rail |

### Detail views

**Character detail** — portrait with upload, name, role, level, disposition, last seen;
AC / HP / Speed; a stat grid (`--surface-elevated` tiles, mono label over Crimson Pro
value); connections list with relationship dots; quote; GM notes. Player characters add a
block with player name, class, race, background, XP, pronouns, and bonds.

**Faction detail** — name, type, influence, reach, motto, goal, members, connections,
GM notes.

### Settings

`max-width: 1080px`, two columns `1fr 1fr`, gap `26px 28px`, `align-items: start`;
collapses to one column ≤900px.

- **Left — Account.** Card `--surface-raised`, `1px --border-subtle`, `--radius-card`.
  Avatar upload; inner `1fr 1fr` grid with Display name and Table/group paired, Email
  spanning `grid-column: 1/-1`. Inputs 40px, `--radius-input`.
- **Right — AI Gateway.** No provider selector — the LLM Gateway routes through OpenRouter
  to a zero-retention allowlist, which is configuration rather than a user choice
  ([ADR-0019](../adr/adr-0019-openrouter-privacy-routing.md)). A green-tinted callout
  (`--success-wash`, `--success-border`, check icon) explains that requests route through
  the gateway to privacy-safe models only.
- Footer actions: Cancel (ghost) and Save changes (accent), right-aligned.

## 5. Knowledge Graph

- Nodes are characters and factions; edges are coloured by relationship kind
- A legend lists all five relationship colours
- **Search** highlights matching nodes and dims the rest
- **Hover** pops an info card with relationship, role, faction, and level
- **Click** navigates to that entity's detail view

v1 renders real relationship data and supports search, hover, and navigation. Editing
relationships from the graph is deferred (see [mvp-scope.md](../mvp-scope.md)).

## 6. Mobile (≤900px)

- Nav rail hidden; main becomes a single column with bottom padding for the tab bar
- **Bottom tab bar** — fixed, `--tabbar-height`, `rgba(14,16,21,.94)` with
  `backdrop-filter: blur(14px)`, top border `1px --border-subtle`. Five items: Home,
  NPCs, Party, Quests, More. Active `--accent`, inactive `--text-muted`
- **More sheet** — bottom sheet, `--surface-raised`, rounded top `--radius-rail`, grab
  handle, `rise` entrance, dimming backdrop. Rows: Factions, Documents, Knowledge Graph,
  Sessions
- **AI panel** — right slide-over, `--panel-width-mobile`,
  `transform: translateX(0 | 105%)` over `--transition-slideover`, with backdrop.
  A 54px round accent FAB at `bottom: 80px` opens it
- Grid reflows: stats → 2 columns, stat block → 3 columns, settings → 1 column,
  player detail → 1 column at ≤560px

Layout mode is tracked in JS as well as CSS, because it changes behaviour: the AI panel
defaults **open on desktop** and **closed on mobile**.

## Interaction rules

- **Transitions** — rail `.26s`, slide-over `.3s`, hover `.15s`, all on `--ease`
- **Backdrops** — `--backdrop` with `blur(2px)`; clicking dismisses
- **Hover depth** — cards lift border colour toward `--border-emphasis`
- **Focus** — inputs move their border to `--accent`
- **Scroll** — 9px custom scrollbar, `--scrollbar-thumb`, transparent track

## Adventure Creator

Creative mode ([ADR-0012](../adr/adr-0012-two-ai-modes.md)) has its own page, designed in
the same prototype:

**▶ [Open the interactive design](https://claude.ai/code/artifact/a7d4de30-0826-4747-b295-a584fe6f0f28)**

It covers the adventure editor, the list, the clue board, the empty state, an AI proposal
awaiting acceptance, and mobile — plus the two distinctions the page lives or dies on:
read-aloud versus GM-private text, and AI draft versus accepted content.

## Gaps requiring design

Listed in [mvp-scope.md](../mvp-scope.md) and repeated here as build blockers:

1. Upload interaction and its immediate feedback
2. Extraction `Failed` state and retry
3. Empty states for a new campaign — the first thing a new user sees
4. How a citation renders inside an assistant bubble
