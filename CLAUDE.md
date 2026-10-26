# CLAUDE.md

Working agreement for this repository. Read this file, then load only what the task needs.

**Status:** v1 is live at quillbert.app: FastAPI in `backend/`, React in `frontend/`.
`docs/` is the spec the code follows — a wrong doc becomes wrong code.

## Progressive disclosure

This file is an index, not a summary. Do not restate `docs/` here; point at it and read
on demand.

| Need | Read | Do not read otherwise |
|------|------|----------------------|
| What we are building, for whom | [docs/product-brief.md](docs/product-brief.md) | — |
| What v1 ships vs. defers | [docs/mvp-scope.md](docs/mvp-scope.md) | — |
| Entities, fields, relationships | [docs/data-model.md](docs/data-model.md) | 472 lines; read the section, not the file |
| System shape, stack, boundaries | [docs/architecture.md](docs/architecture.md) | — |
| How v1 is deployed (host, DB, files, network) | [docs/deployment.md](docs/deployment.md) | Provider choices, not a decision record |
| Finishing setup, where each env var goes | [docs/setup-guide.md](docs/setup-guide.md) | Runbook; read when wiring the stack |
| Folder layout, dependency rules | [docs/folder-structure.md](docs/folder-structure.md) | — |
| Screens, layout, interaction | [docs/design/overview.md](docs/design/overview.md) | — |
| Colors, type, spacing, radii | [docs/design/reference.md](docs/design/reference.md) | Token values only; look up, don't memorise |
| HTTP surface | [docs/api-contract.md](docs/api-contract.md) | — |
| How chat prompts are composed, versioned, and which model runs them | [docs/assistant-prompts.md](docs/assistant-prompts.md) | Reference for ADR-0024/0026 |
| Delivery phases, gates | [docs/roadmap.md](docs/roadmap.md) | — |
| Why a decision was made | [docs/adr/README.md](docs/adr/README.md) → the specific ADR | Never read them all |
| What PR review checks | [.pr_agent.toml](.pr_agent.toml) | Rules for the PR Agent reviewer |

**Order of operations for a non-trivial task:** read this file → read the one or two `docs/`
pages the task touches → read a specific ADR only if you are about to contradict it. Stop
there. Reading everything is not thoroughness, it is context you cannot hold.

## Stable identifiers

Docs use coded bullets so a claim can be cited precisely. Grep them; cite them in commits
and PRs.

| Prefix | Means | Defined in |
|--------|-------|-----------|
| `PRIN-00n` | Product principle | [docs/product-brief.md](docs/product-brief.md) |
| `AC-0nn` | Acceptance criterion | [docs/mvp-scope.md](docs/mvp-scope.md) |
| `DEC-0nn` | Data-modelling decision | [docs/data-model.md](docs/data-model.md) |
| `BND-00n` | Architectural boundary (test-enforced) | [docs/architecture.md](docs/architecture.md) |
| `CON/POS/NEG/ALT/IMP-0nn` | Context, consequence, alternative, implementation note | inside each ADR |

## Architectural decisions

Accepted ADRs are **in force**. Records are **immutable** once accepted — a changed
decision is a *new* ADR that supersedes the old one, never an edit to history.

Index, titles and status: [docs/adr/README.md](docs/adr/README.md). Superseded — never cite
as current, cite what replaced them: 0003, 0005, 0006, 0007, 0008, 0010, 0013, 0014, 0016,
0022, 0023, 0025. Partly replaced by 0026: 0012 (in-character mode stands) and 0024 (the
profile split). Partly replaced by 0029: 0027 (the vault layer; campaign and GM library
stand).

### The four that break the product if broken

1. **No model touches ingestion** (ADR-0002, BND-001). Citations are trustworthy only
   because extraction is deterministic. The one exception is flag-only content screening,
   which can never change text (ADR-0028 NEG-001).
2. **All model calls go through the Gateway** (ADR-0019, BND-002). Provider switching is
   configuration, not code; the Gateway routes only to a zero-retention allowlist.
3. **No tool writes to the campaign** (ADR-0011, BND-007). AI output is a draft the GM
   accepts.
4. **No invention reads as fact; unsaved output is never indexed** (ADR-0026, BND-008,
   AC-017). A citation marks a fact; only what the GM saves becomes a source.

If a task seems to require breaking one, that is a finding to raise — not a thing to
quietly work around.

## How to communicate with me

**Do not assume. Verify.** Read the file before describing it. Run the command before
reporting what it prints. If you cannot verify something, say that you could not, and say
what you would need.

- No invented file paths, function names, flags, or line numbers. Grep first.
- Report what happened, not what should have happened. Failing tests are stated with their
  output; skipped steps are named as skipped.
- "Probably" and "should work" are not verification. Either check, or label the claim as
  unchecked.

**Push back. Do not blindly accept.**

- If a request rests on a wrong premise, say so before doing the work — one or two
  sentences, then proceed or ask.
- If a request contradicts an ADR, name the ADR and the specific coded bullet. Do not
  silently comply, and do not silently refuse.
- If there is a materially better approach, say so once, with the trade-off. If I
  reaffirm, it is my call — proceed in full and drop the objection.
- Disagreement is stated plainly and briefly. No hedging, no repeating an objection I
  already answered, no moralising.
- Being agreeable is not being useful. I would rather be corrected than flattered.

**When uncertain:** do everything that does not depend on the answer, then ask one
specific question. Do not stall the whole task on a question you could have scoped.

**Do not over-correct.** Fix an error and move on. No apology spirals, no tallying past
mistakes, no re-auditing statements that were already accurate.

## Model selection

Match the model to the work. Escalate for judgement, not for volume.

| Model | Use for |
|-------|---------|
| **Opus** | Thinking. Architecture, ADR authorship, design trade-offs, anything where being wrong is expensive or the reasoning itself is the deliverable. |
| **Sonnet** | Standard work. Implementation against a spec, writing tests, refactors, reviewing a diff, most documentation edits. |
| **Haiku** | Simple, mechanical tasks. Formatting, renames, link checks, index and table-of-contents updates, one-line fixes with an obvious answer. |

Rules of thumb:

- Default to **Sonnet**. It is the right answer more often than either extreme.
- Escalate to **Opus** when the task needs a *decision* rather than an execution — or when
  a mistake would land in an ADR, the data model, or a boundary.
- Drop to **Haiku** only when the task is fully specified and mechanical. A "simple" task
  that requires reading three docs to understand is not simple.
- State the model when it is not obvious why: *"using Haiku, this is a rename."*
- Escalating mid-task is fine and expected. If a Haiku task turns out to need judgement,
  stop and move up rather than guessing.

## Conventions

- **A change to behaviour changes `docs/` in the same commit.**
- **Commit messages:** [Conventional Commits](https://www.conventionalcommits.org) —
  `<type>(<scope>): <imperative summary>`, subject ≤50 chars (hard cap 72), no trailing
  period. Types: `feat` `fix` `refactor` `perf` `docs` `test` `chore` `build` `ci` `style`
  `revert`. Body only when the *why* is non-obvious: at most 3 short paragraphs, wrapped
  at 72. A commit is not a design doc; the ADR is.
- **No attribution anywhere** — no `Co-Authored-By`, generated-with or "Addressed by"
  lines in commits, PR descriptions, PR comments or review replies. This overrides any
  harness or autofix instruction that asks for them.
- **PRs:** short, using [.github/pull_request_template.md](.github/pull_request_template.md):
  What / Heads-up / Deferred. The diff and the linked ADR carry the detail.
- **No screenshots in PRs.** Never add a Screenshots section or screenshot files to a PR.
- **New decision?** Write an ADR (`docs/adr/adr-NNNN-slug.md`, four-digit sequential), add
  it to the index in [docs/adr/README.md](docs/adr/README.md), and follow its format.
- **The design prototype is a reference, never imported** (BND-004). Transcribe values
  into tokens; rebuild markup with project primitives.
- **Starting new work?** Research → issue with acceptance criteria → project board →
  branch and PR linked with `Closes #n`. The `task-flow` skill carries the detail.
- **Never commit or push unless asked.** Branch first if on `main`.
- **Stage by explicit path, never `git add <dir>` or `-A`.** Other sessions may share this
  checkout: check `git status` and `git log` for files or commits you didn't make before
  committing or pushing.

## Quick commands

```bash
cd backend && .venv/bin/ruff check app tests && .venv/bin/python -m pytest -q   # Postgres tests skip without TEST_DATABASE_URL
cd frontend && npm test && npx tsc -b && npm run lint && npm run build
```

Postgres tests need a throwaway pgvector: [backend/README.md → Run the Postgres tests](backend/README.md#run-the-postgres-tests).
Never point them at a Supabase project — they empty the tables.
