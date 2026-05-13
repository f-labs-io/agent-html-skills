---
name: html-mind-map
description: Create branching, draggable HTML mind maps and concept maps for capturing brainstorms, mapping knowledge structures, exploring debugging hypotheses, or organizing nested ideas. Always include a Submit button (calls `submitToClaude`) to send the captured structure back to the agent for next steps. Use whenever the user wants to capture, organize, or explore branching ideas, hypotheses, knowledge structures, or any tree/graph-shaped thinking — especially when they say "brainstorm", "map out", "explore", or "what if".
---

# HTML Mind Map & Concept Map

Some thinking is tree-shaped or graph-shaped: brainstorming variations of an idea, mapping a knowledge domain, working through "what if X is the cause" debugging trees, or organizing nested concepts. A mind map externalizes that structure so the user can see it, rearrange it, and hand it back to the agent for the next step.

## ⚙️ Pre-flight — run BEFORE writing the artifact

This skill produces an interactive artifact. **Invoke the `html-skills-listen` skill from this plugin first** (Skill tool: `html-skills:html-skills-listen`). It sets up a per-session local receiver and arms a `Monitor` so user submissions arrive as session notifications instead of as copy-paste round-trips. It's idempotent — invoke every time you fire this skill.

Capture the URL it returns. If it returned one, inject it as `window.__CLAUDE_SUBMIT_URL__` in the HTML you're about to write. If it reported web/sandbox mode (no URL returned), generate the HTML *without* `__CLAUDE_SUBMIT_URL__` set — `submitToClaude` will fall back to clipboard mode automatically.

Skipping this step costs the user a copy-paste round-trip on every submit. Invoking the skill is cheap and idempotent.


## When to use this skill

- "Brainstorm / map out / explore X"
- "What are all the possibilities for Y"
- "Help me think through the causes of Z"
- "Organize these ideas / concepts / hypotheses"
- "Build me a concept map for X"
- Any explanation that branches recursively

## Output requirements

Nodes draggable. New nodes addable inline. Connections between nodes (most often a tree, sometimes a graph). Always include an export button that produces a structured representation of the map — JSON tree, indented outline, or natural-language summary.

The map starts populated with whatever the user provided as starting nodes; the user expands from there.

## HTML output foundation

These defaults apply to **every** artifact this skill produces, on top of the requirements above. If a rule above conflicts with this list, the rule above wins; otherwise these are non-negotiable.

- **Output a real `.html` file the user opens in a browser — never inline-render in chat.** Every artifact this skill produces is a file on disk (`<topic>-<kind>.html`), not an HTML block embedded in the agent's chat surface (claude.ai artifact/canvas widgets, fenced ```html``` blocks, custom rendered iframes, etc.). Inline rendering strips features, themes unpredictably against the surrounding chat (often unreadable in dark mode), and lacks the stable origin and clipboard/network access the submit handler needs. Always write the file. The file itself must be self-contained: no build step, no external runtime, inline CSS and JS. Google Fonts via `<link>` is fine; otherwise nothing loaded from npm or a CDN unless this skill explicitly calls for it.
- **Mobile-responsive.** Collapse cleanly to a single column under ~700px so the artifact opens on a phone — including during incidents, commutes, and link-shares to non-laptop reviewers.
- **No `localStorage` / `sessionStorage` / `IndexedDB`.** Claude.ai artifacts can't use browser storage. State lives in JS memory; the export / copy button is the persistence layer.
- **Real semantic HTML, not screenshots.** Code goes in `<pre><code>` (selectable, copyable). Tabular data goes in `<table>`. Diagrams are inline `<svg>` with real `<g>` and `<path>` elements, not embedded PNGs. The reader should be able to copy any value, line, or label out of the artifact.
- **Build DOM safely; don't sling strings.** Use `textContent` for text and `document.createElement` + `appendChild` for structure. **Never** set `innerHTML` from a string that includes a variable, user input, computed value, or imported data — it's an XSS vector and many agent harnesses (including Claude Code) block it via security hooks. Static literal markup inline in your script is fine.
- **SVG text doesn't wrap — size the shape to the label, or use `<foreignObject>`.** Plain SVG `<text>` overflows silently when the label is longer than the box was sized for, crashing into adjacent shapes. For variable-length or potentially-long labels, wrap with `<foreignObject width="W" height="H">` plus an HTML `<div>` inside — real wrapping, real padding, real `text-overflow:ellipsis`. Plain `<text>` is fine only for short, fixed-length labels — and even then, size the surrounding shape from the label length (≥ 8px per char + 16px padding each side at 14px), not the other way around. The `html-svg-diagrams` skill has the full pattern; reach for it whenever a diagram is more than a few words.
- **CSS variables for theme tokens.** Centralise colors, type, and spacing in `:root` so the whole artifact can be re-skinned in one place — and so design decisions are visible, not buried in 40 inline declarations.
- **Pick a deliberate aesthetic; skip the generic AI look.** No default purple gradient + Inter + three centered feature cards. Match the visual direction to the document's domain (utilitarian for ops, editorial for writeups, engineering for diagrams, etc.). Distinctive type pairings beat default sans on default sans.
- **Print- and PDF-readable.** `Cmd/Ctrl+P` should produce something usable: backgrounds that carry meaning print, content doesn't get clipped, dark themes have a sane print fallback.
- **Accessible by default.** Body text meets WCAG AA contrast. Interactive controls are keyboard-reachable and have visible focus states. Status and severity are conveyed by shape/label too, not color alone.
- **Visible last-updated timestamp** in the footer for any artifact someone might revisit (specs, diagrams, reports, roadmaps, dashboards). One-shot editors and ephemeral playgrounds can skip it.
- **Filename is part of the artifact.** Save with a descriptive name (`<topic>-<kind>.html`) so multiple artifacts on one project compose into a readable folder, not a pile of `output.html` collisions.

## Submit pipeline (server or clipboard)

This skill produces an interactive artifact whose value is in what the user submits back. There are exactly two delivery modes:

| Mode | Setup | Use when |
|---|---|---|
| **Server** (default in local Claude Code) | Run the `html-skills-listen` skill once per session — it prints a per-session URL like `http://127.0.0.1:<ephemeral-port>/`. Inject `window.__CLAUDE_SUBMIT_URL__ = '<that URL>'` into each artifact. Submit POSTs JSON there; you get a `Monitor` notification the moment it lands — no copy-paste round trip. | You are in a local Claude Code session with shell access. This is almost always you when there's a real terminal. |
| **Clipboard** (fallback) | None. Inline `submit-handler.js` and call `submitToClaude(payload)`. Submit copies JSON; user pastes back. | the `html-skills-listen` skill reported it can't run (cloud / web / sandboxed harness), or the harness has no `Monitor`-equivalent. Always works, but every submit costs the user a paste. |

**One decision rule:** *before producing the first interactive artifact in a session*, run the `html-skills-listen` skill. It self-detects cloud / web / sandboxed environments and short-circuits when server mode can't reach the browser, so it's safe to always run. If it reports active, inject `window.__CLAUDE_SUBMIT_URL__` in every artifact you generate this session. If it short-circuited, drop to clipboard mode and don't retry. Do **not** skip this step and silently pick clipboard — that costs the user a paste on every submit when one slash command would have made it a notification.

Server mode automatically falls through to clipboard if the POST fails for any reason, so the user is never stuck.


### Inlining the submit handler

Every interactive artifact must inline `$CLAUDE_PLUGIN_ROOT/assets/submit-handler.js` inside a `<script>` block, and wire its submit / export button to call `submitToClaude(payload)`:

```html
<button id="submit">Submit to Claude</button>
<script>
  // …contents of $CLAUDE_PLUGIN_ROOT/assets/submit-handler.js pasted here…
</script>
<script>
  // OPTIONAL — only set when in server mode. Absence = clipboard mode.
  // window.__CLAUDE_SUBMIT_URL__ = 'http://127.0.0.1:<port-from-the `html-skills-listen` skill>/';

  document.getElementById('submit').addEventListener('click', async () => {
    await submitToClaude({
      skill: 'html-<this-skill-name>',
      kind:  '<artifact-kind>',          // e.g. "kanban-result", "mind-map-tree", "matrix-verdict"
      data:  collectStateAsPlainObject(),
      version: 1,
    });
  });
</script>
```

### Standardised payload envelope

Both modes carry the same JSON:

```json
{
  "skill":   "html-mind-map",
  "kind":    "mind-map-tree",
  "data":    { /* skill-specific structure */ },
  "version": 1
}
```

`data` is whatever the skill's existing export produces. The other fields are routing.


### Anti-patterns

- Inventing a third "sometimes-works" mode by probing the network from the artifact. Server or clipboard, nothing in between.
- Inventing surface-specific submit bridges (`sendPrompt()`, `postMessage` to the parent frame, magic global functions you saw work in some other context). The contract is two modes: POST to `__CLAUDE_SUBMIT_URL__` if set, otherwise clipboard. The artifact lives at a `file://` or `localhost:` origin and the chat surface isn't reachable from there. Don't guess at a third path — clipboard always works.
- Omitting the submit button on the assumption that clipboard isn't useful, or because the artifact is being inline-rendered in a chat surface. Clipboard mode IS the delivery; the button must always exist and always call `submitToClaude(payload)`. The user clicks once, JSON copies, they paste back at the next chat turn — that's the whole flow.
- Inline-rendering the artifact inside the agent's chat surface instead of writing a real `.html` file. See the foundation rule — always write the file.
- Putting two clipboard buttons on the artifact (e.g. "Copy as prompt" + "Submit"). One Submit button per artifact, period. It calls `submitToClaude(payload)`, which copies the JSON envelope. If you want the user's eventual chat message to read like a prompt with context, generate that prompt server-side from the JSON envelope after they paste — don't fork the export into two affordances on the page. The user shouldn't have to choose which button does what.
- Calling `navigator.clipboard.writeText(...)` directly from any button handler. The plugin exposes two helpers — `submitToClaude` for the structured submission and `copyToClipboard(text, opts)` for any other clipboard write (a "copy this URL" button, a "copy CSS" button, etc.). Both share the same async-API → execCommand → inline-banner fallback chain, so they never strand the user with "can't copy". Direct `navigator.clipboard.writeText` calls bypass the fallbacks and break in the same Safari `file://` / iframe-Permissions-Policy contexts the helpers were built for.
- Skipping the `html-skills-listen` skill and going straight to clipboard mode in a local Claude Code session. The user has to copy-paste every submit when one slash command would have made it a `Monitor` notification. Always run the `html-skills-listen` skill first; it self-detects when to short-circuit, so there's no "but what if I'm in the wrong environment" — running it is the right call regardless.
- Hand-rolling the receiver setup when the `html-skills-listen` skill exists. Use the slash command in Claude Code; only use the manual recipe in non-Claude-Code harnesses.
- Different payload shapes per skill. Use the standard envelope so a result-handling agent can be skill-agnostic.
- Forgetting to call the `html-skills-stop` skill when the task is done.

## Core structure

1. **Canvas** — the main interactive area where nodes live
2. **Root / starting node** — central, larger, anchored
3. **Branches** — child nodes radiating outward (or hanging downward)
4. **Connections** — lines (sometimes labeled) showing parent-child or relational links
5. **Toolbar** — add node, delete, reset, export
6. **Export panel** — produces the map's content as text

## Patterns

### Pattern A: Brainstorm capture

Tree shape, root in the center, ideas radiate. New ideas added by clicking a parent + "+". Loose — branches don't need to be balanced. Color-coded by category if useful (e.g., features in blue, risks in red, questions in yellow).

Export: an indented outline, ready to paste back as a prompt.

### Pattern B: Knowledge map

For organizing a domain. Hierarchical tree, often with cross-links between distant nodes (a true graph, not a pure tree). Nodes have short titles; click to see longer description in a side panel. Useful for mapping an unfamiliar codebase, an API surface, or a topic.

Export: JSON tree, suitable for feeding to a documentation generator.

### Pattern C: Debugging tree / hypothesis explorer

For "what could be causing X". Root is the symptom. Children are hypotheses. Each hypothesis has children for evidence (✓ supports, ✗ refutes), tests to run, and sub-hypotheses. Branches that get refuted are visually pruned but kept for record.

Export: a structured debugging journal with the surviving hypotheses + evidence.

### Pattern D: Decision tree

For walking through a multi-step decision. Root is the question. Branches are options. Each option's children are sub-questions, consequences, or further options. Often used for runbook-style "if X, do Y" content.

Export: a flowchart-like markdown or an actual runbook outline.

### Pattern E: Concept relationships (graph, not tree)

For when relationships aren't strictly hierarchical (e.g., "this concept relates to that one in two different ways"). Nodes connect with labeled edges. Force-directed layout. Useful for showing systems of interacting ideas.

Export: an adjacency list or DOT graph.

## Interaction

- **Drag** to reposition nodes
- **Click + plus icon** to add a child
- **Double-click a node** to edit text
- **Right-click / long-press** for delete, color, mark
- **Pan** the canvas (drag background) and **zoom** (scroll/pinch)
- **Keyboard**: `Tab` to add child, `Enter` to add sibling, `Delete` to remove (Workflowy-like)

## Layout

For tree-shaped maps:
- **Horizontal tree** (root on left, branches to the right) — feels like an outline with visual structure
- **Radial** (root in center, branches in a circle) — feels like a brainstorm
- **Vertical** (root at top, branches downward) — feels like a hierarchy

For graph-shaped maps:
- **Force-directed** — nodes repel, connections attract; produces organic layouts
- **Manual** — user positions nodes; connections follow

Pick a default and let the user toggle if it matters.

## Visual style

Avoid the corporate-mindmap aesthetic (rainbow gradients, clip art, MS Office vibes). Better defaults:

- **Soft & analog** — paper-like background, hand-drawn-feeling lines, warm neutrals
- **Editorial** — confident type, two-color palette, generous whitespace
- **Engineering** — monospace labels, dark theme, single accent color, crisp lines

The map's purpose informs the style. Brainstorms benefit from a softer feel; debugging trees benefit from technical clarity.

## Export formats

The export is what makes the map useful beyond the session. Offer multiple shapes:

**Indented outline** (most universal):
```
- Caching strategies
  - In-memory LRU
    - + simple
    - − doesn't survive restarts
  - Redis
    - + persistent
    - − ops cost
```

**JSON tree** (for programmatic use):
```json
{ "title": "Caching strategies", "children": [...] }
```

**Natural-language prompt** (for handing back to the agent):
```
Here's the map I built. The root is "caching strategies" with three approaches…
```

## Anti-patterns

- Mind maps that can't be edited. Static visualizations are less useful than interactive maps for this use case.
- Forgetting export. Without it, the map is trapped in the artifact.
- Heavy library dependencies for a tool that should be lightweight.
- Forcing tree shape when the data is graph-shaped (or vice versa).
- Auto-layouts that fight the user's manual positioning.

## Example prompt

> Help me brainstorm names for our new internal AI tool. Build me a mind map starting with three branches: "literal & functional", "evocative & poetic", "playful & weird". Pre-fill each branch with 3–4 starter names. Let me add more, color-mark favorites, and export the final list as a prompt I can hand back.

Output: HTML file with a radial mind map, three colored branches with 3–4 starter nodes each, drag-to-reposition, click-plus-to-add-child, double-click-to-edit, right-click for color/delete/favorite, and a Submit-to-Claude button.

Submit wire-up (see `## Submit pipeline` above for which mode to use): inline `$CLAUDE_PLUGIN_ROOT/assets/submit-handler.js`, then call:
```js
submitToClaude({
  skill: 'html-mind-map',
  kind: 'mind-map-tree',
  data: {
    root: 'naming the AI tool',
    branches: [
      { label: 'literal & functional', color: 'blue', favorites: ['Tabby', 'Atlas'], all: [...] },
      { label: 'evocative & poetic',  color: 'amber', favorites: ['Glimpse'], all: [...] },
      { label: 'playful & weird',     color: 'green', favorites: [], all: [...] },
    ],
  },
  version: 1,
});
```
