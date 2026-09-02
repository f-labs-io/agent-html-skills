# html-skills

Seventeen Claude Code skills for HTML-output patterns — derived from Thariq's article ["Using Claude Code: The Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935) — plus two session primitives (`html-skills-listen`, `html-skills-stop`) that send results from the page back to Claude.

## What's in here

| # | Skill | Use when |
|---|---|---|
| 01 | `html-spec-planning` | Specs, RFCs, implementation plans, exploration |
| 02 | `html-code-review` | PR explainers, refactor risk maps, codebase tours (PR-explainer pattern folded in) |
| 03 | `html-design-prototypes` | Component design, animation tuning, design systems |
| 04 | `html-research-reports` | Multi-source research synthesis, status reports, incidents |
| 05 | `html-throwaway-editor` | One-off editors that send the edited result back to Claude |
| 06 | `html-interactive-playground` | Sliders/knobs for parameter tuning, two-way interaction |
| 07 | `html-brainstorm-grid` | N-variant comparison grids with tradeoff labels |
| 08 | `html-svg-diagrams` | Flowcharts, sequence diagrams, state machines |
| 09 | `html-slideshow-deck` | Keyboard-navigable presentation decks |
| 10 | `html-design-tokens` | Color/type/spacing token showcases (the article's anti-markdown example) |
| 11 | `html-architecture-diagrams` | System maps, deployment topologies |
| 12 | `html-data-explorer` | Filterable tables, faceted search, log viewers |
| 13 | `html-comparison-matrix` | Weighted decision matrices |
| 14 | `html-timeline-roadmap` | Gantt/roadmap/timeline views |
| 15 | `html-erd-explorer` | Database schema visualizations |
| 16 | `html-mind-map` | Branching concept maps that send the tree back |
| 17 | `html-testing-checklist` | Flow-organized testing checklists that send pass/fail results back |

## Design notes

- **Skills are markdown-only; runtime assets are plugin-level**, not per-skill. The skills are about communication patterns and aesthetic guidance, not deterministic transforms; a single `SKILL.md` is the right shape. The shared submit receiver (`server.js`, bundled with the `html-skills-listen` skill) and the submit-handler JS (`assets/submit-handler.js`) live at the plugin root and are referenced by every skill — see "Submit pipeline" below.
- **Pushy descriptions** — each frontmatter `description` is written to fight Claude's tendency to undertrigger. They include explicit phrases ("brainstorm", "compare", "diagram") so the skill triggers even when the user doesn't say "HTML". Trigger phrases that don't fit live in `when_to_use`, a Claude Code frontmatter field the router reads alongside `description` (the pair is truncated at 1,536 characters in the skill listing; skills.sh shows only the description, which stays under 1,024).
- **Shared blocks, repeated by tooling** — every content skill carries the same `## Pre-flight`, `## HTML output foundation`, and (interactive skills) `## Submit pipeline` sections verbatim, because skills are loaded independently and skills.sh reads one `SKILL.md` at a time. They are not hand-maintained: the templates live in `assets/blocks/`, each copy sits between `<!-- block:… -->` markers, and `scripts/sync-skills.py --write` re-syncs them (`--check` fails CI on drift).
- **Browser storage is a reload guard, not a data store** — `localStorage` is allowed under a per-artifact key prefix (`html-skills:<skill>:<artifact-slug>:`) so pages never read each other's state; masked secrets are never stored; Submit/export is still the delivery.

## Submit pipeline for interactive artifacts

Seven skills produce artifacts the user submits back: `html-throwaway-editor`, `html-mind-map`, `html-brainstorm-grid`, `html-comparison-matrix`, `html-interactive-playground`, `html-design-prototypes`, `html-testing-checklist`. Each of those `SKILL.md` files ends with a `## Submit pipeline (server or clipboard)` block describing the contract. Every content skill runs the same pre-flight, because the "Publish to Claude.ai" button (below) uses the same channel.

### Two modes

| Mode | Setup | When to use |
|---|---|---|
| **Server** (default in local Claude Code) | Agent invokes the `html-skills-listen` skill from each content skill's pre-flight block — it returns a per-session URL like `http://127.0.0.1:<ephemeral-port>/?t=<session-handshake>`. The agent injects `window.__CLAUDE_SUBMIT_URL__ = '<that URL>'` into each artifact at generation time, exactly as returned — the `?t=` value is how the receiver rejects forged POSTs; never strip the query string. Submit POSTs JSON there; agent gets a `Monitor` notification — no copy-paste. | Agent is in a local Claude Code session with shell access. Almost always you when there's a real terminal. |
| **Clipboard** (fallback) | None. Artifact inlines `assets/submit-handler.js` and calls `submitToClaude(payload)`. Submit copies JSON; user pastes back. | `html-skills-listen` reported it can't run (cloud / web / sandboxed harness), or the harness has no `Monitor`-equivalent. Always works, but every submit costs the user a paste. |

The decision rule for agents is one line: *before writing each artifact*, invoke the `html-skills-listen` skill (it's idempotent). It self-detects cloud/web/sandboxed environments and short-circuits when server mode can't reach the browser, so it's always safe to run. If it reports active, use server mode for every artifact this session. If it short-circuited, drop to clipboard. Server mode falls through to clipboard if a POST fails for any reason, and the toast says the listener didn't answer, so the user is never stuck or misled.

If the receiver dies (a tab closed mid-POST used to crash it — fixed in 1.3.0), the next pre-flight restarts it with the same handshake value and, when free, the same port, so earlier artifacts keep working; if the port had to change, the agent tells the user.

### What ships in the plugin

- **`skills/html-skills-listen/`** — Self-contained skill that sets up server mode. Bundles `server.js` (zero-dependency Node HTTP listener on an ephemeral port; emits each submission as one JSON line on stdout) and `scripts/listen.sh` (self-locating bash that handles startup, idempotency, restarts, and stale-session cleanup). The skill's SKILL.md instructs Claude to run the script, arm a `Monitor` on its log, and return the URL to the parent skill. It is `user-invocable: false` — Claude calls it; it stays out of the `/` menu.
- **`assets/submit-handler.js`** — The two-mode submit JS, inlined into every artifact via copy-paste from the SKILL block. Picks server vs clipboard based on whether `window.__CLAUDE_SUBMIT_URL__` is set; never probes the network speculatively. Also exposes `copyToClipboard` for every other copy button.
- **`assets/blocks/`** — Templates for the shared SKILL.md sections (see Design notes). Authoring-time only; nothing reads them at runtime.
- **`skills/html-skills-stop/`** — Paired teardown skill. Runs a short bash script, then stops the `Monitor` saved by `html-skills-listen` via `TaskStop`. Both setup and teardown skills detect `$CLAUDE_CODE_REMOTE_SESSION_ID` and short-circuit cleanly in cloud sessions.

### Where each mode works

| Environment | Server | Clipboard | Recommended setup |
|---|---|---|---|
| Claude Code CLI / IDE / Desktop (local) | ✅ | ✅ | invoke `html-skills-listen` from each skill's pre-flight, inject the returned URL as `__CLAUDE_SUBMIT_URL__` in the artifact |
| Local SDK harness without `Monitor`-equivalent | ❌ | ✅ | None — submit always copies to clipboard |
| **Claude Code on the web** (`claude.ai/code`) | ❌ | ✅ | None. Generate the file, tell the user to open it locally (`claude --teleport <session-id>` is cleanest); submit copies JSON to clipboard; user pastes back at next chat turn |
| Sandboxed / no-shell agent | ❌ | ✅ | None — submit always copies to clipboard |

### Manual recipe (for non-Claude-Code harnesses)

The bundled script does everything and prints `KEY=VALUE` lines, including the full URL with its `?t=` handshake:

```bash
bash $CLAUDE_PLUGIN_ROOT/skills/html-skills-listen/scripts/listen.sh my-session-id
# … STATUS=STARTED
# … URL=http://127.0.0.1:<port>/?t=<handshake>
```

Or by hand:

```bash
node $CLAUDE_PLUGIN_ROOT/skills/html-skills-listen/server.js > /tmp/html-skills-submits.log 2>&1 &
echo $! > /tmp/html-skills-submits.pid
sleep 0.3
grep -oE 'listening on http://127\.0\.0\.1:[0-9]+/\?t=[^[:space:]]+' /tmp/html-skills-submits.log | tail -1 | sed 's/listening on //'
```

The server defaults to an ephemeral port; the `grep` extracts the whole URL — keep the `?t=` query string, the receiver rejects POSTs without it. Arm your live-tail equivalent on the log, filtering for `"method":"notifications/claude/channel"`. Inject `window.__CLAUDE_SUBMIT_URL__ = '<the URL grep printed>'` into the artifact. (Pin a specific port by exporting `HTML_SKILLS_CHANNEL_PORT=8788` before launching, if you prefer.)

### Standardised payload envelope

Both modes carry the same JSON, so a result-handling agent can be skill-agnostic:

```json
{
  "skill":   "html-mind-map",
  "kind":    "mind-map-tree",
  "data":    { /* skill-specific structure */ },
  "version": 1
}
```

`data` is whatever the skill's structure produces. The other fields are routing.

One additional standard kind is shared by every content skill: `kind: "publish-request"`, emitted by the "Publish to Claude.ai" button (see the foundation block's last bullet). Its `data.file` names the artifact the user wants published via the `Artifact` tool; agents honor it only for files they generated in the current session, and publish a copy with the submit URL and the button stripped.

## Skill boundaries

A few skills cover adjacent territory and need explicit disambiguation. The descriptions encode these boundaries; this section documents them in one place for reviewers.

### `html-brainstorm-grid` ↔ `html-comparison-matrix`

Both deal with multiple options. The boundary is the **phase of cognition** the user is in:

| Signal in the prompt | Phase | Skill |
|---|---|---|
| Candidates are NOT named ("brainstorm", "show me approaches", "what are the ways") | Generative — *create* candidates | `html-brainstorm-grid` |
| Candidates ARE named ("compare X, Y, Z" / "should we use A or B") | Evaluative — *score* candidates | `html-comparison-matrix` |

The single test: **are specific candidates named in the prompt?** If not, generate them with the grid. If so, score them with the matrix. The two skills are designed to compose — explore in the grid, then evaluate the survivors in the matrix.

### `html-brainstorm-grid` ↔ `html-mind-map` ↔ `html-spec-planning`

All three hear "brainstorm". The mind map captures and rearranges the *user's own* ideas as an editable tree; the grid renders N distinct alternatives *Claude generates* for side-by-side comparison; spec-planning writes the document once a direction exists. `html-spec-planning` deliberately doesn't list "brainstorm" as a trigger.

### Other adjacencies (lower-risk)

- `html-svg-diagrams` is the general diagram skill; `html-architecture-diagrams` and `html-erd-explorer` are specific ones. The specific ones should win when the prompt names a system or schema.
- `html-spec-planning` and `html-research-reports` overlap on "explain X" — spec is forward-looking (what we'll build), research is descriptive (how X works).

## Untouched

The following four skills from the original catalog were left unselected and aren't here: Test Coverage Reports, Internal Documentation Hubs, Distributed Trace/Log Viewers, ADR Browser. Annotated PR Code Explainers was folded into `html-code-review` as patterns A and D.

---

Source: Thariq @trq212, "The Unreasonable Effectiveness of HTML."

## Copyright

Copyright © 2026 Fiverr Labs.

Created with ♥ by Fiverr Labs.
