# Design Tokens

Transcribed from the design prototype. These values are **authoritative** — components
reference tokens, never literals.

## Color

### Surfaces

| Token | Value | Used for |
|-------|-------|----------|
| `--surface-app` | `#0A0C0F` | App background, header |
| `--surface-sunken` | `#0d0f14` | Inputs, AI panel background |
| `--surface-raised` | `#12141A` | Cards, nav rail, assistant bubbles |
| `--surface-elevated` | `#1A1D25` | Raised buttons, tag chips |
| `--surface-hover` | `#22262F` | Hover states, stat tiles |
| `--gradient-stop-a` | `#151821` | Landing radial gradient |
| `--gradient-stop-b` | `#1A1E28` | Login radial gradient |

### Borders

| Token | Value | Used for |
|-------|-------|----------|
| `--border-subtle` | `#1E2027` | Card and panel dividers |
| `--border-default` | `#22262F` | Inputs, chips |
| `--border-strong` | `#262A33` | Nav rail, mobile sheet |
| `--border-emphasis` | `#2E3340` | Raised buttons, hover borders |

### Text

| Token | Value | Used for |
|-------|-------|----------|
| `--text-primary` | `#F8FAFC` | Headings, body |
| `--text-secondary` | `#CBD5E1` | Supporting copy |
| `--text-muted` | `#64748B` | Labels, meta, placeholders |

### Accent and status

| Token | Value | Used for |
|-------|-------|----------|
| `--accent` | `#E8B87A` | Primary actions, active nav, focus |
| `--accent-hover` | `#F5D4A6` | Link hover |
| `--accent-glow-soft` | `rgba(232,184,122,.28)` | Primary button shadow |
| `--accent-glow-strong` | `rgba(232,184,122,.4)` | Mobile FAB shadow |
| `--accent-wash` | `rgba(232,184,122,.1)` | Active filter chip background |
| `--success` | `#7FD4A0` | Indexed status, tool chips, provider dot |
| `--success-wash` | `rgba(127,212,160,.06)` | Gateway callout background |
| `--success-border` | `rgba(127,212,160,.2)` | Gateway callout border |

### Relationship colors

Used consistently across NPC cards, faction cards, graph edges, and connection lists.

| Token | Value | Meaning |
|-------|-------|---------|
| `--rel-ally` | `#7FD4A0` | Ally |
| `--rel-enemy` | `#EF7777` | Enemy |
| `--rel-family` | `#E8B87A` | Family |
| `--rel-professional` | `#7BA3D6` | Professional |
| `--rel-neutral` | `#6B6F76` | Neutral |

A `showRelationshipColors` setting collapses all of these to `--rel-neutral`.

### Other

| Token | Value | Used for |
|-------|-------|----------|
| `--quest-subquest` | `#8B6FC4` | Subquest tiles |
| `--scrollbar-thumb` | `#2E3340` | Scrollbar (hover `#3a404e`) |
| `--backdrop` | `rgba(6,8,11,.6)` | Modal and slide-over backdrop, `blur(2px)` |

Google brand glyph colors (login only): `#4285F4`, `#34A853`, `#FBBC05`, `#EA4335`.

## Typography

| Token | Stack |
|-------|-------|
| `--font-display` | `'Crimson Pro', Georgia, serif` |
| `--font-body` | `'Inter', system-ui, sans-serif` |
| `--font-mono` | `'JetBrains Mono', monospace` |

**Crimson Pro** — brand, page titles, entity names, stat values.
**Inter** — all UI text.
**JetBrains Mono** — eyebrow labels, uppercase, `letter-spacing: .06em`, ~12px.

### Sizes observed

| Use | Size / weight |
|-----|---------------|
| Brand wordmark (login) | 27px / 600 Crimson Pro |
| Page title | 30px Crimson Pro |
| Section heading | 20px Crimson Pro |
| Rail brand | 15px / 600 Crimson Pro |
| Body | 13–14px Inter |
| Secondary / meta | 11–13px |
| Tab bar label | 10.5px / 600 |
| Stat value | 18px / 600 Crimson Pro |
| Stat label | 10px / 500 JetBrains Mono |

## Radii

| Token | Value | Used for |
|-------|-------|----------|
| `--radius-sm` | `6px` | Tag chips, tool chips |
| `--radius-md` | `8px` | Icon buttons, quick-prompt chips |
| `--radius-lg` | `9px` | Filter chips, scrollbar |
| `--radius-input` | `10px` | Inputs, settings fields |
| `--radius-button` | `11px` | Buttons, avatars, connection rows |
| `--radius-card` | `14px` | Settings cards, chat composer |
| `--radius-brand` | `17px` | Login brand tile |
| `--radius-panel` | `18px` | Login card |
| `--radius-rail` | `20px` | Nav rail, mobile sheet top |
| `--radius-bar` | `4px` | Progress bars |
| `--radius-thumb` | `7px` | Document type tile |
| `--radius-tile` | `12px` | Document rows, icon tiles |
| `--radius-zone` | `16px` | Upload drop zone |

Assistant bubbles: `14px 14px 14px 4px` (assistant) / mirrored for user.

## Shadows

| Token | Value | Used for |
|-------|-------|----------|
| `--shadow-card` | `0 30px 80px rgba(0,0,0,.5)` | Login card |
| `--shadow-rail-collapsed` | `0 12px 30px rgba(0,0,0,.5)` | Nav rail, collapsed |
| `--shadow-rail-expanded` | `0 30px 80px rgba(0,0,0,.75)` | Nav rail, expanded |
| `--shadow-slideover` | `-24px 0 60px rgba(0,0,0,.6)` | Mobile AI panel |
| `--shadow-sheet` | `0 -24px 60px rgba(0,0,0,.6)` | Mobile More sheet |
| `--shadow-accent` | `0 6px 20px rgba(232,184,122,.28)` | Primary button |
| `--shadow-fab` | `0 8px 28px rgba(232,184,122,.35)` | Desktop assistant pill |
| `--shadow-fab-mobile` | `0 10px 30px rgba(232,184,122,.4)` | Mobile assistant FAB |

## Layout

| Token | Value |
|-------|-------|
| `--header-height` | `72px` |
| `--rail-width-collapsed` | `60px` |
| `--rail-width-expanded` | `236px` |
| `--rail-column` | `76px` (grid column reserving rail space) |
| `--rail-offset-left` | `24px` |
| `--panel-width` | `400px` |
| `--panel-width-mobile` | `min(420px, 100vw)` |
| `--tabbar-height` | `calc(64px + env(safe-area-inset-bottom))` |
| `--main-padding` | `28px 32px 48px` (desktop) |
| `--main-padding-mobile` | `20px 18px calc(90px + env(safe-area-inset-bottom))` |

Workspace grid: `grid-template-columns: 76px minmax(0,1fr) <400px|0>`, rows
`72px` then content. Header spans all columns with `padding: 0 20px 0 100px` — the left
padding clears the floating rail.

## Motion

| Token | Value | Used for |
|-------|-------|----------|
| `--ease` | `cubic-bezier(.4,0,.2,1)` | All transitions |
| `--transition-rail` | `width .26s var(--ease), padding .26s` | Rail expand/collapse |
| `--transition-slideover` | `transform .3s var(--ease)` | Mobile AI panel |
| `--transition-fast` | `all .15s` | Hover states |

Keyframes:

```css
@keyframes rise   { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:none } }
@keyframes blink  { 0%,100% { opacity:1 } 50% { opacity:0 } }
@keyframes dotpulse { 0%,60%,100% { transform:translateY(0); opacity:.4 }
                      30% { transform:translateY(-4px); opacity:1 } }
```

`rise` — entrance for sheets and cards. `blink` — streaming cursor (7×15px accent block).
`dotpulse` — typing indicator, three dots staggered `0` / `.2s` / `.4s`.

## Breakpoints

| Width | Effect |
|-------|--------|
| `≤900px` | Mobile shell: rail hidden, bottom tab bar, AI panel becomes slide-over, stat grid → 2 columns, stat block → 3 columns, settings → 1 column |
| `≤560px` | Player detail grid → 1 column |

The prototype also tracks `mob` in JS via a `resize` listener at the same 900px threshold,
because layout mode changes behaviour (panel defaults closed on mobile), not just styling.

## Background gradients

| Screen | Value |
|--------|-------|
| Login | `radial-gradient(circle at 50% -10%, #1A1E28, #0A0C0F 55%)` |
| Campaign picker | `radial-gradient(circle at 50% 0%, #151821, #0A0C0F 60%)` |

Placeholder imagery (campaign banners, portraits) uses diagonal stripe gradients between
two surface colors until a user image is uploaded.
