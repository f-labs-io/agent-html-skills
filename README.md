# agent-html-skills

**Two-way HTML artifacts for Claude Code — Claude generates the page, you interact with it in your browser, and the result comes back to Claude automatically. No copy-paste.**

Thariq's article ["Using Claude Code: The Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935) made the case for HTML as a better output surface than long-form markdown — color, layout, type, interactivity, all the things markdown gives up. This plugin runs with that idea and closes the loop: six of the sixteen skills produce *interactive* HTML (mind maps, kanban editors, brainstorm grids, comparison matrices, parameter playgrounds, design prototype tuners), and when you click Submit, your structured result is delivered back to Claude as a notification in the same session. You move on without copying anything.

The mechanism is a per-session local listener that the `html-skills-listen` skill arms automatically — the interactive skills invoke it from their pre-flight block before writing the artifact. If you skip it, or you're on Claude Code on the web, the same Submit button gracefully falls back to copying JSON to your clipboard for paste-back — so the artifacts always work, you just lose the "automatic" part of the round-trip. The other ten skills are non-interactive artifacts (specs, diagrams, dashboards, decks, design tokens, etc.) where there's no result to send back; they just produce the file.

Sixteen skills total. Each is a single `SKILL.md` with the aesthetic rules and structural guidance baked in, so the output looks deliberate rather than generic-AI.

## Install

```text
/plugin marketplace add f-labs-io/agent-html-skills
/plugin install html-skills@agent-html-skills
```

## What you get

| # | Skill | Use when |
|---|---|---|
| 01 | `html-spec-planning` | Specs, RFCs, implementation plans, exploration |
| 02 | `html-code-review` | PR explainers, refactor risk maps, codebase tours |
| 03 | `html-design-prototypes` | Component design, animation tuning, design systems |
| 04 | `html-research-reports` | Multi-source research synthesis, status reports, incidents |
| 05 | `html-throwaway-editor` | One-off editors that send results back to Claude |
| 06 | `html-interactive-playground` | Sliders/knobs for tuning parameters |
| 07 | `html-brainstorm-grid` | N-variant comparison grids when exploring options |
| 08 | `html-svg-diagrams` | Flowcharts, sequence diagrams, state machines |
| 09 | `html-slideshow-deck` | Keyboard-navigable presentation decks |
| 10 | `html-design-tokens` | Color/type/spacing token showcases |
| 11 | `html-architecture-diagrams` | System maps, deployment topologies |
| 12 | `html-data-explorer` | Filterable tables, faceted search, log viewers |
| 13 | `html-comparison-matrix` | Weighted decision matrices for named candidates |
| 14 | `html-timeline-roadmap` | Gantt / roadmap / timeline views |
| 15 | `html-erd-explorer` | Database schema visualizations |
| 16 | `html-mind-map` | Branching concept maps that send the tree back |

You don't invoke these directly — Claude will reach for the right one when the task fits. Each artifact is written to a `.html` file you open in your browser.

## Enabling the auto round-trip

For the auto-submit path to work in a local Claude Code session, run this once per session:

Claude invokes the bundled **`html-skills-listen` skill** automatically before producing any interactive artifact in a local Claude Code session — you don't have to do anything. It arms a per-session local listener on an ephemeral port and a `Monitor` on its log; every Submit click then lands directly in Claude as a notification, no manual copy-paste. When you're done, Claude can invoke `html-skills-stop` to tear it down (or just end the session — the receiver dies with the shell).

Skip the command and you stay on the clipboard fallback; the artifacts still work, you just paste the JSON back yourself.

## Using these skills in Claude.ai chat (not Claude Code)

The content of each skill — aesthetic guidance, structure rules, foundation, anti-patterns — is platform-agnostic. Only the *submit pipeline* in the six interactive skills is Claude-Code-specific (it relies on a local server, `Monitor`, and slash commands). With that stripped out, every skill works as a regular Claude.ai skill at **Settings → Capabilities → Skills**, with HTML written to a file you save and open in your browser, and interactive results copied to your clipboard for paste-back.

### Asking Claude.ai's skill-creator to repackage

Open a Claude.ai chat with [skill-creator](https://claude.com/plugins/skill-creator) active and paste this prompt verbatim:

> Repackage the skills in `https://github.com/f-labs-io/agent-html-skills/tree/main/plugins/html-skills/skills` as individual Claude.ai skills — one `.skill` file per `SKILL.md`. Follow the **Conversion spec for skill-creator** section of that repo's top-level README exactly. Strip every Claude-Code-only mechanism (slash commands, MCP server, `Monitor`, server mode, `__CLAUDE_SUBMIT_URL__`). Keep all content guidance, aesthetic rules, the `## HTML output foundation` block, and the clipboard path of `assets/submit-handler.js`. Produce one `.skill` per skill so users can install only the ones they want.

### Conversion spec for skill-creator

**Source layout** (read these files from the repo):

```
plugins/html-skills/
├── skills/<skill-name>/SKILL.md      ← 16 of these, one per skill
└── assets/submit-handler.js          ← inlined by the 6 interactive skills
```

**For every skill (all 16):**

1. Keep the frontmatter `name` and `description`. The `description` field is "pushy" by design (per the [skill-creator authoring guide](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)) — don't soften it.
2. From the body, strip the `**TRIGGER: about to populate AskUserQuestion...**` prefix sentence in `html-brainstorm-grid`, `html-design-prototypes`, and `html-comparison-matrix`. That trigger is specific to Claude Code's `AskUserQuestion` tool — Claude.ai's chat surface doesn't have it as a competing comparison primitive, so the rule is noise there. Keep everything else in those skills' bodies (the actual generation guidance and the anti-patterns about visual comparison).
3. Keep the `## HTML output foundation` block at the end unchanged.
4. Keep all other body content and anti-patterns unchanged.

**For the 6 interactive skills only** (`html-mind-map`, `html-throwaway-editor`, `html-brainstorm-grid`, `html-comparison-matrix`, `html-interactive-playground`, `html-design-prototypes`):

5. Replace the `## Submit pipeline (server or clipboard)` section with a single shorter section titled `## Submit (clipboard)`. Body should be: *"On submit, JSON copies to the user's clipboard for them to paste back into Claude. There is no server mode in Claude.ai chat — don't reference one. Inline the `submit-handler.js` from `assets/` and call `submitToClaude(payload)` from the single Submit button. Do not set `window.__CLAUDE_SUBMIT_URL__` — leaving it unset is what selects clipboard mode."*
6. Place `submit-handler.js` (the unmodified file from the repo's `plugins/html-skills/assets/`) into the packaged skill's `assets/` folder. The handler already gracefully falls back to clipboard when `__CLAUDE_SUBMIT_URL__` is unset, so no code change is needed — it Just Works in Claude.ai.
7. Keep these interactive-skill anti-patterns intact: one Submit button per artifact (no parallel "copy as prompt" buttons), never call `navigator.clipboard.writeText` directly (use `submitToClaude` / `copyToClipboard` for the hardened fallback chain), no inline-rendering inside Claude's chat surface (always write a real `.html` file), no `innerHTML` from variables (XSS / security-hook trip).
8. Drop interactive-skill anti-patterns that name Claude-Code-only surfaces: anything about `html-skills-listen`, `Monitor`, ephemeral ports.

**Drop entirely (don't include in any `.skill` package):**

- `commands/listen.md`, `commands/stop.md` — Claude.ai has no slash commands
- `channel/server.js`, `.mcp.json` — Claude.ai has no MCP
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — Claude Code plugin manifests

**Package each skill:**

Use skill-creator's `scripts/package_skill.py` (or the equivalent zip-the-folder step) to produce one `.skill` file per skill, named `html-<kind>.skill`. The user installs each via Settings → Capabilities → Skills in Claude.ai.

**Package contents per skill:**

```
html-<kind>/
├── SKILL.md          ← converted per rules above
└── assets/
    └── submit-handler.js   ← only for the 6 interactive skills
```

The non-interactive 10 skills don't need an `assets/` folder.

## License

MIT — see [LICENSE](./LICENSE).

## Copyright

Copyright © 2026 Fiverr Labs.

Created with ♥ by Fiverr Labs.
