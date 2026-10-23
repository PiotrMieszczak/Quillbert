# Design Tokens

Transcribed from the design prototype. These values are **authoritative** — components
reference tokens, never literals. The code is `frontend/src/styles/tokens.css`.

Two themes: dark is the default (`:root`), light applies on `<html data-theme="light">`.
Where a token has no light value it is the same in both.

## Color

### Surfaces

| Token | Dark | Light | Used for |
|-------|------|-------|----------|
| `--surface-app` | `#0A0C0F` | `#F4F1EB` | Page background, button ink on accent |
| `--surface-sunken` | `#0D0F14` | `#F8F6F1` | Inputs, AI panel background |
| `--surface-raised` | `#12141A` | `#FFFFFF` | Cards, nav rail, composer, citation chips |
| `--surface-elevated` | `#1A1D25` | `#F0ECE5` | Raised buttons, user chat bubble, action hover |
| `--surface-hover` | `#22262F` | `#DCD5CA` | Hover states, stat tiles |
| `--surface-subtle` | `#151821` | `#FAF7F2` | Nav rail item hover |
| `--gradient-stop-b` | `#1A1E28` | `#F0ECE5` | Placeholder stripes |

### Borders

| Token | Dark | Light | Used for |
|-------|------|-------|----------|
| `--border-subtle` | `#1E2027` | `#E3DDD3` | Card and panel dividers |
| `--border-default` | `#22262F` | `#DCD5CA` | Inputs, chips, composer |
| `--border-strong` | `#262A33` | `#D5CDC1` | Nav rail, mobile sheets |
| `--border-emphasis` | `#2E3340` | `#C6BDAF` | Raised buttons, hover and focus borders |
| `--border-hover` | `#3A404E` | `#B2A899` | Scrollbar thumb hover |
| `--border-emphasis-hover` | `#5A6270` | `#7F766A` | Login Google button, hover |

### Text

| Token | Dark | Light | Used for |
|-------|------|-------|----------|
| `--text-primary` | `#F8FAFC` | `#1C1916` | Headings, body |
| `--text-secondary` | `#CBD5E1` | `#3A342D` | Supporting copy |
| `--text-muted` | `#8D97A9` | `#665E54` | Labels, meta, placeholders (6.4:1 on `--surface-app`) |
| `--text-faint` | `#5C6474` | `#958B7D` | Decorative and disabled only, never body copy |

### Accent and status

| Token | Dark | Light | Used for |
|-------|------|-------|----------|
| `--accent` | `#E8B87A` | `#94560F` | Primary actions, active nav, focus, streamed-word ink |
| `--accent-hover` | `#F5D4A6` | `#74400A` | Link hover, card sheen |
| `--accent-wash` | `rgba(232,184,122,.1)` | `rgba(148,86,15,.1)` | Active chip, spark tiles |
| `--success` | `#7FD4A0` | `#1D7444` | Indexed status, completed reading steps, "Copied" |
| `--success-wash` | `rgba(127,212,160,.06)` | `rgba(29,116,68,.06)` | Gateway callout background |
| `--success-border` | `rgba(127,212,160,.2)` | `rgba(29,116,68,.2)` | Gateway callout border |

There are no accent glows: buttons and FABs carry no coloured shadow.

### Relationship colors

Used consistently across NPC cards, faction cards, graph edges, and connection lists.

| Token | Dark | Light | Meaning |
|-------|------|-------|---------|
| `--rel-ally` | `#7FD4A0` | `#1D7444` | Ally |
| `--rel-enemy` | `#EF7777` | `#BE3838` | Enemy; also errors |
| `--rel-family` | `#E8B87A` | `#94560F` | Family |
| `--rel-professional` | `#7BA3D6` | `#2D61A4` | Professional |
| `--rel-neutral` | `#868B94` | `#6B645B` | Neutral |

A `showRelationshipColors` setting collapses all of these to `--rel-neutral`.

### Other

| Token | Dark | Light | Used for |
|-------|------|-------|----------|
| `--quest-subquest` | `#8B6FC4` | `#6A4FB0` | Subquest tiles |
| `--scrollbar-thumb` | `#2E3340` | `#C6BDAF` | Scrollbar (hover `--border-hover`) |
| `--scrim` | `10 12 15` | `250 248 243` | RGB triplet for translucent layers: `rgb(var(--scrim) / .72)` |
| `--backdrop` | `rgb(var(--scrim) / .6)` | — | Modal and sheet backdrop, no blur |
| `--surface-tabbar` | `rgb(var(--scrim) / .94)` | — | Mobile tab bar |

Nothing uses `backdrop-filter`: a translucent layer sits on a scrim, never a blur.

Google brand glyph colors (login only): `#4285F4`, `#34A853`, `#FBBC05`, `#EA4335`.

## Typography

Loaded from Google Fonts in `frontend/index.html`.

| Token | Stack |
|-------|-------|
| `--font-display` | `'Newsreader', Georgia, serif` |
| `--font-body` | `'Hanken Grotesk', system-ui, sans-serif` |
| `--font-mono` | `'JetBrains Mono', monospace` |

**Newsreader** — brand, page titles, entity names, stat values, Quillbert's name.
**Hanken Grotesk** — all UI text.
**JetBrains Mono** — eyebrow labels (uppercase, `letter-spacing: .06em`, ~12px), keycaps,
citation chips.

### Sizes observed

| Use | Size / weight |
|-----|---------------|
| Brand wordmark (login) | 27px / 600 Newsreader |
| Page title | 30px Newsreader |
| Section heading | 20px Newsreader |
| Rail brand | 17px / 600 Newsreader |
| Body | 13–14px Hanken Grotesk |
| Assistant reply | 14px / 1.65 |
| Secondary / meta | 11–13px |
| Citation chip | 11.5px / 500 JetBrains Mono |
| Tab bar label | 10.5px / 600 |
| Stat value | 18px / 600 Newsreader |
| Stat label | 10px / 500 JetBrains Mono |

## Radii

| Token | Value | Used for |
|-------|-------|----------|
| `--radius-sm` | `6px` | Tag chips |
| `--radius-md` | `8px` | Icon buttons, error-card buttons |
| `--radius-lg` | `9px` | Filter chips, scrollbar, panel rail button |
| `--radius-input` | `10px` | Inputs, settings fields |
| `--radius-button` | `11px` | Buttons, avatars, theme toggle, reading tile |
| `--radius-card` | `14px` | Settings cards, chat composer |
| `--radius-brand` | `17px` | Login brand tile |
| `--radius-panel` | `18px` | Login card, campaign cards |
| `--radius-rail` | `20px` | Nav rail, mobile sheet top |
| `--radius-bar` | `4px` | Progress bars |
| `--radius-thumb` | `7px` | Document type tile, citation chips, reply actions |
| `--radius-tile` | `12px` | Document rows, icon tiles, error card |
| `--radius-zone` | `16px` | Upload drop zone |

User chat bubble: `14px 14px 4px 14px`. Assistant replies have no bubble.

## Shadows

Shadows are for depth only: no accent glows. They take their colour from `--sh` and their strength from `--sha` (dark `0 0 0` / `1`;
light a warm `60 45 25` / `.22`), so one token reads right in both themes.

| Token | Value | Used for |
|-------|-------|----------|
| `--shadow-card` | `0 20px 50px rgb(var(--sh) / calc(.55 * var(--sha)))` | Login card, hovered campaign card |
| `--shadow-rail-collapsed` | `0 12px 30px … .5` | Nav rail, collapsed |
| `--shadow-rail-expanded` | `0 30px 80px … .75` | Nav rail, expanded |
| `--shadow-sheet` | `0 -24px 60px … .6` | Mobile More sheet, mobile AI panel |

## Layout

| Token | Value |
|-------|-------|
| `--header-height` | `72px` |
| `--rail-width-collapsed` | `60px` |
| `--rail-width-expanded` | `236px` |
| `--rail-column` | `76px` (grid column reserving rail space) |
| `--rail-offset-left` | `24px` |
| `--panel-width` | `400px` |
| `--panel-width-collapsed` | `56px` (the "Ask Quillbert" rail) |
| `--panel-height-mobile` | `86vh` (AI panel bottom sheet) |
| `--tabbar-height` | `calc(64px + env(safe-area-inset-bottom))` |
| `--main-padding` | `28px 32px 48px` (desktop) |
| `--main-padding-mobile` | `20px 18px calc(90px + env(safe-area-inset-bottom))` |

Workspace grid: `grid-template-columns: 76px minmax(0,1fr) <400px|56px>`, rows `72px`
then content. Header spans all columns with `padding: 0 20px 0 100px` — the left padding
clears the floating rail.

## Motion

| Token | Value | Used for |
|-------|-------|----------|
| `--ease` | `cubic-bezier(.4,0,.2,1)` | Transitions |
| `--ease-spring` | `cubic-bezier(.2,.8,.2,1)` | Pops, nav hover, card tilt return |
| `--transition-rail` | `width .26s var(--ease), padding .26s` | Rail expand/collapse |
| `--transition-panel` | `grid-template-columns .28s var(--ease)` | AI panel open/collapse |
| `--transition-sheet` | `transform .3s var(--ease)` | Mobile AI panel |
| `--transition-fast` | `all .15s` | Hover states |

Keyframes (all in `tokens.css`):

| Name | Does | Used for |
|------|------|----------|
| `rise` | fade in from `translateY(8px)` | Views (.3s), live messages (.25s), sheets, error card |
| `blink` | opacity 1 → 0 → 1, `step-end` | Streaming cursor, 7×15px accent block |
| `qb-ink` | opacity 0 in `--accent` → visible → cools to ink | Each streamed word, .9s |
| `qb-pop` | rise with overshoot (`scale .92 → 1.03 → 1`) | Citation chips (.45s, staggered .12s), campaign cards (.6s) |
| `qb-ring` | ring scales `.6 → 2.2` while fading | Reading indicator pulse, 1.8s |
| `qb-scribble` | small rotate/translate wobble | Reading-indicator quill, 1.2s |
| `qb-draw` | `stroke-dashoffset 64 → 0 → -64` | Reading-indicator scribble line, 1.6s |
| `qb-check` | `stroke-dashoffset 14 → 0` | Completed reading step, .4s |
| `qb-flash` | `--accent` wash and outline fading out | Document row a citation chip opened, 2s |
| `qb-spin` | full rotation | Active reading step spinner, .8s linear |
| `qb-bob` | 2px bob with ±2° tilt | Quill mark beside a reply that is still writing, .9s |

Under `prefers-reduced-motion: reduce` every animation and transition runs for `.01ms`
once, the word reveal shows text at once, and the ambient background draws a still frame.

## Breakpoints

| Width | Effect |
|-------|--------|
| `≤900px` | Mobile shell: rail hidden, bottom tab bar, AI panel becomes a bottom sheet with a round FAB, stat grid → 2 columns, stat block → 3 columns, settings → 1 column |
| `≤560px` | Player detail grid → 1 column |

Layout mode is also tracked in JS at the same 900px threshold, because it changes
behaviour (panel defaults closed on mobile), not just styling.

## Backgrounds

Screens have no gradient of their own: the ambient canvas (see
[overview.md](overview.md#ambient-background-and-theme)) draws behind them on
`--surface-app`.

Placeholder imagery (campaign banners, portraits) uses diagonal stripe gradients between
two surface colors until a user image is uploaded.
