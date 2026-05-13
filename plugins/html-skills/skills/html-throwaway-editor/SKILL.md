---
name: html-throwaway-editor
description: Build single-purpose, throwaway HTML editors for one specific piece of data — drag-and-drop boards, form-based config editors, side-by-side prompt tuners, dataset curators, annotation tools. Always end with a Submit button (calls `submitToClaude`) so the result can be sent back to the agent. Use whenever the user wants to triage, reorder, edit, annotate, curate, prioritize, or pick values where typing prose would be tedious — Linear tickets, feature flags, prompts, datasets, transcripts, anything.
---

# HTML Throwaway Editor

When describing what you want to do is harder than just doing it, build a one-off editor. Not a product. Not a reusable tool. A single HTML file purpose-built for this one piece of data, with an export button at the end that turns the result back into something pasteable.

## ⚙️ Pre-flight — run BEFORE writing the artifact

This skill produces an interactive artifact. **Invoke the `html-skills-listen` skill from this plugin first** (Skill tool: `html-skills:html-skills-listen`). It sets up a per-session local receiver and arms a `Monitor` so user submissions arrive as session notifications instead of as copy-paste round-trips. It's idempotent — invoke every time you fire this skill.

Capture the URL it returns. If it returned one, inject it as `window.__CLAUDE_SUBMIT_URL__` in the HTML you're about to write. If it reported web/sandbox mode (no URL returned), generate the HTML *without* `__CLAUDE_SUBMIT_URL__` set — `submitToClaude` will fall back to clipboard mode automatically.

Skipping this step costs the user a copy-paste round-trip on every submit. Invoking the skill is cheap and idempotent.


## When to use this skill

- "I need to reprioritize / reorder / triage these N things"
- "Help me edit / curate / annotate / tag this dataset"
- "I want to tune / pick / configure these values" (where the values aren't simple text)
- "Build me a quick editor for X"
- Any time the user describes a manipulation that would be painful to do in chat but easy with a UI

## Output requirements

Pre-populate with the actual data the user provided — never make them paste it again. End with an export button that copies a structured representation to the clipboard: JSON, markdown, or a natural-language prompt.

The export is non-negotiable. An editor without export is a dead-end; "throwaway" means the result lives outside the artifact, not inside it.

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

1. **Header** — what this editor is for, and a link/note showing when work is unsaved
2. **Editing surface** — the actual UI
3. **Live state preview** (optional but useful) — a sidebar or footer showing the current state as JSON
4. **Export panel** — copy button(s), preferably with format options

## Patterns

### Pattern A: Drag-and-drop board (Kanban-style)

For reordering, triaging, or bucketing. Columns like "Now / Next / Later / Cut" or "Approved / Rejected / Unsure". Cards are draggable. Counter per column. Pre-sort intelligently if you can guess the user's intent.

Export: ordered list per column with a one-line rationale field per item.

### Pattern B: Form-based config editor

For structured config (feature flags, env vars, JSON/YAML with constraints). Group fields by area. Show dependencies between fields — warn if enabling A requires B that's currently off. Highlight changes from the original. Export only the diff, not the whole config.

### Pattern C: Side-by-side prompt/template editor

Editable input on the left, live preview on the right with the variables filled in. Multiple sample inputs to switch between. Token/char counter. Highlight variable slots in the input.

### Pattern D: Dataset curator

For approve/reject workflows on rows. Big yes/no buttons or keyboard shortcuts (j/k, y/n). Filtered list of remaining items. Show counts: "37 to review, 12 approved, 4 rejected". Export the labeled set.

### Pattern E: Annotation tool

For document/transcript/diff annotation. Click a span to add a note. Tags or color categories. Export annotations as a structured list with source quotes.

### Pattern F: Value picker

For things painful to express in text — colors, easing curves, crop regions, cron schedules, regexes. Visual picker UI with live preview of what the value does. Export the chosen value in the format the user needs (CSS, code, etc.).

If the user wants to *explore a parameter space* (sweep through values, compare A/B, find the sweet spot through tuning), use `html-interactive-playground` instead. This pattern is for picking one value with a visual control; the playground is for tuning behavior across many values.

## Export conventions

The copy button should make it dead-easy to paste back into Claude Code. Two common shapes:

**Copy as JSON** — for structured data that another session will parse:
```json
{ "ordered": ["ENG-101", "ENG-87", ...], "rejected": ["ENG-203"] }
```

**Copy as prompt** — for natural-language hand-off:
```
Apply these reorderings to Linear:
- Move to Now: ENG-101, ENG-87 (most blocking)
- Move to Cut: ENG-203 (deprioritized)
```

Offer both when both make sense.

## Keyboard ergonomics

If the user is going to do this for more than a few items, add keyboard shortcuts. Common ones:
- `j` / `k` — next / previous item
- `1`–`9` — assign to bucket N
- `enter` — confirm
- `cmd+c` (custom-handled) or a visible button — export

Show the shortcuts in a small "?" panel.

## Anti-patterns

- Saving state to localStorage. Throwaway means throwaway. State lives in memory; export is the persistence layer.
- A "Save" button that doesn't do anything. The button must export.
- Building generic infrastructure. This is one-shot. Hardcode for the data you have.
- Asking the user to enter the data. They already gave it to you — pre-populate.

## Example prompt

> I need to reprioritize these 30 Linear tickets [pasted list]. Make me an HTML file with each ticket as a draggable card across Now / Next / Later / Cut columns. Pre-sort them by your best guess. Add a "copy as markdown" button that exports the final ordering with a one-line rationale per bucket.

Output: HTML file with four columns, 30 pre-sorted draggable cards, counters per column, and a Submit-to-Claude button at the bottom.

Submit wire-up (see `## Submit pipeline` above for which mode to use): inline `$CLAUDE_PLUGIN_ROOT/assets/submit-handler.js`, then call:
```js
submitToClaude({
  skill: 'html-throwaway-editor',
  kind: 'kanban-reorder',
  data: { now: [...ids], next: [...ids], later: [...ids], cut: [...ids], rationale: { 'ENG-101': 'most blocking', ... } },
  version: 1,
});
```
