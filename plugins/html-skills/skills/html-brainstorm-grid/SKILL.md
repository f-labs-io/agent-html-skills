---
name: html-brainstorm-grid
description: >-
  **TRIGGER: about to populate `AskUserQuestion` options with `preview:` content for any visual / UX / layout / screen / component / mockup comparison.** STOP and ask first: *"Quick inline chip comparison, or a full HTML grid you can open in the browser?"* Chips flatten color, type, density, motion, and interaction into monospace; HTML grids preserve all of it. **No carve-out for "simulate", "demo", "mock up", "quick decision", "just for now" — those name the surface, not an exception.** When user picks HTML, this skill generates side-by-side grids of N distinctly-different approaches — for the GENERATIVE phase, when candidates are NOT yet named. Use when the user signals exploration: "brainstorm", "explore options", "show me variations", "different approaches", "I'm not sure how to…", "try a few directions". GENERATE candidates, don't score known ones. If specific candidates ARE named ("compare X, Y, Z" / "should we use A or B"), hand off to html-comparison-matrix.
---

# HTML Brainstorm Comparison Grid

When the user is undecided between approaches, the strongest move is a grid of distinctly different options laid out side-by-side, each labeled with the tradeoff it makes. The grid forces contrast — if two options are too similar, one of them isn't pulling its weight.

> **Phase boundary.** This skill handles the *generative* phase of comparison — generating candidates the user hasn't named yet. Once specific candidates exist and the question shifts to "which one wins on these criteria", hand off to `html-comparison-matrix`. The boundary signal is whether candidates appear in the prompt: if not, generate them here; if so, score them there. The two skills are designed to compose — explore here, then evaluate there.

## ⚙️ Pre-flight — run BEFORE writing the artifact

This skill produces an interactive artifact. **Invoke the `html-skills-listen` skill from this plugin first** (Skill tool: `html-skills:html-skills-listen`). It sets up a per-session local receiver and arms a `Monitor` so user submissions arrive as session notifications instead of as copy-paste round-trips. It's idempotent — invoke every time you fire this skill.

Capture the URL it returns. If it returned one, inject it as `window.__CLAUDE_SUBMIT_URL__` in the HTML you're about to write. If it reported web/sandbox mode (no URL returned), generate the HTML *without* `__CLAUDE_SUBMIT_URL__` set — `submitToClaude` will fall back to clipboard mode automatically.

Skipping this step costs the user a copy-paste round-trip on every submit. Invoking the skill is cheap and idempotent.


## When to use this skill

- "Generate a few approaches for X"
- "I'm not sure which direction to take"
- "Show me variations / alternatives / options"
- "Compare directions for X before I commit"
- "Try different X" (where X is layout, naming, structure, tone, etc.)
- Any time the user is exploring rather than committing

## When NOT to use this skill

- The user names specific candidates ("compare React, Vue, Svelte"). Use `html-comparison-matrix`.
- The user has already chosen and just wants to score the choice. Use `html-comparison-matrix`.
- The output is a single recommendation rather than a set of alternatives. Use `html-spec-planning`.

## Output requirements

A grid of 3–6 cells. Each cell renders an actual instance of the option (not a description of it). Each cell has a label naming the tradeoff. The grid is the artifact — no long preamble, no conclusion section.

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

- Silently picking between `AskUserQuestion`'s `preview` field and a full HTML grid for a visual comparison. Both have real costs — the chip is one tool call but flattens color/type/density/motion/interaction into monospace text; the HTML grid is a real file + Submit round-trip but preserves all of that. The user is in the best position to pick. When the comparison is visual/UX/layout-shaped, ask one short question first: "quick inline chip or full HTML grid?" Then honor the answer. Don't default to whichever feels easier to *you* — the easier path for the agent (preview chip) is often the worse path for the user (when the choice is visual).

- Rationalizing a skip because the user framed the request as "simulate", "demo", "mock up", "quick decision", "just for now", "what would you suggest", or similar lightweight phrasing. The framing identifies the *surface* (a visual UI/UX comparison), not an *exception* to the ask-first rule. The rule fires on the surface, not on the phrasing.
- Locking into `AskUserQuestion` mentally before the skill-check gate fires, then reading the html-skills "ask first" rule as off-topic to your already-chosen path. The moment you're about to fill in `preview:` with anything resembling a UI mockup IS the trigger — stop there, not earlier. The rule lives on the trigger ("about to populate `preview:` for a visual comparison"), not on the skill's primary purpose.
- Underweighting the cost asymmetry. Asking is ONE extra question. Skipping when the user wanted HTML is a FULL REDO — discarded ASCII previews, fresh HTML file, new submission round-trip, plus the user-side annoyance of having to redirect. 1 question vs N steps + frustration. Always ask.
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

## The distinctness mandate

Three near-duplicates is worse than two contrasting options. Vary along multiple axes at once:

- For UI layouts: vary **layout** (vertical/horizontal/grid), **density** (sparse/dense), **emphasis** (which element dominates), **tone** (formal/playful/utilitarian)
- For naming: vary **register** (literal/evocative/playful), **length**, **etymology** (Latin/Germanic/coined)
- For architecture: vary **shape** (monolith/split/event-driven), **state location** (client/server/edge), **coupling** (sync/async/batch)

If two cells could be reasonably described in the same sentence, collapse them into one and add a more contrasting alternative.

## Core structure

1. **Header** — what was varied, what wasn't (the constants)
2. **Grid** — N cells, each with:
   - The actual rendered option
   - A short label for the tradeoff ("simplest, no cancel" / "abort on retype, +0 deps" / "library, 12kb dep")
   - A pros/cons or +/− list (1–2 lines)
3. **Choose button per cell** (optional) — when the user picks, export which one and why

## Patterns

### Pattern A: UI variant grid

For visual design exploration. 4–6 cells, each rendering a different layout for the same content. Tradeoff labels under each. Same content, different layouts.

### Pattern B: Architectural alternative grid

For technical decisions. 3–4 cells, each a small diagram + bullet list. Tradeoff labels in big text on each cell. Often paired with a comparison matrix below.

### Pattern C: Copy/naming grid

For text variations. Smaller cells, more options (6–10). Each cell shows the variant in context — not just the word, but the word in the actual UI it would live in.

### Pattern D: Configuration sweep

For "what if we did X with these parameters". Small multiples — same chart/diagram with different inputs. Tradeoff labels indicate what changes between cells.

## Layout conventions

- **3 options**: horizontal row
- **4 options**: 2×2 grid
- **6 options**: 2×3 or 3×2 grid
- **More than 6**: reconsider — probably collapsing some makes the comparison sharper

Each cell should be the same size. Inconsistent sizing implies hierarchy where there shouldn't be any. Use a clear monospace label for the tradeoff so it's easy to scan across the row.

## Tradeoff labeling

The label is what makes the grid useful. Bad labels: "Option A", "Variant 2". Good labels: "minimal, no animation", "playful but heavier", "matches existing system", "fastest to ship, hardest to extend".

The label should answer: "what does this one give up, what does it gain?"

## Optional: choose-and-export

When the user picks one, capture that choice + a brief rationale and offer to copy it as a prompt:

```
I'm going with option C ("library, 12kb dep") — willing to take the bundle hit for the cancellation handling.
Now help me implement it in the actual codebase.
```

## Anti-patterns

- Five options that are visually identical with one detail changed. That's parameter tuning, not exploration — use the playground skill instead.
- Cells with placeholder content. Render real content so the comparison is meaningful.
- A "winner" picked for the user. The grid's job is to show options; let the user choose.
- Cells of different sizes implying ranking. The grid is for comparison, not recommendation.

## Example prompt

> I'm not sure what direction to take the onboarding screen. Generate 6 distinctly different approaches — vary layout, tone, and density — and lay them out as a single HTML file in a grid so I can compare them side by side. Label each with the tradeoff it's making.

Output: HTML file with a 2×3 or 3×2 grid of 6 onboarding screens, each rendered as actual UI, each labeled with one-line tradeoffs underneath, with a "pick this one" button per cell and a final Submit-to-Claude button.

Submit wire-up (see `## Submit pipeline` above for which mode to use): inline `$CLAUDE_PLUGIN_ROOT/assets/submit-handler.js`, then call:
```js
submitToClaude({
  skill: 'html-brainstorm-grid',
  kind: 'pick-one',
  data: {
    chosen: 'C',
    title: 'Vertical, dense, utilitarian',
    tradeoff_label: 'fastest to read, no delight',
    rationale: '<optional user text>',
    candidates: ['A', 'B', 'C', 'D', 'E', 'F'],
  },
  version: 1,
});
```
