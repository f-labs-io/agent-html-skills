---
name: html-interactive-playground
description: Create HTML playgrounds with sliders, knobs, toggles, and live preview for tuning algorithm parameters, animation values, design tokens, layout dimensions, or any value that's painful to express in text. Always include a Submit button (calls `submitToClaude`) so chosen values can be sent back to Claude Code. Use whenever the user wants to experiment with values, fine-tune behaviors, explore a parameter space, or pick from a continuous range — debounce timings, color values, easing curves, threshold values, layout dimensions, anything tunable.
---

# HTML Interactive Playground

Some values are easier to find by feel than by reasoning — animation timings, easing curves, color combinations, threshold values, layout dimensions. A playground turns the parameter space into a UI: sliders for continuous values, dropdowns for discrete ones, live preview, and a copy-back button.

This is the two-way interaction pattern: the user explores in the browser, then copies what worked back to the agent to apply for real.

## ⚙️ Pre-flight — run BEFORE writing the artifact

This skill produces an interactive artifact. **Invoke the `html-skills-listen` skill from this plugin first** (Skill tool: `html-skills:html-skills-listen`). It sets up a per-session local receiver and arms a `Monitor` so user submissions arrive as session notifications instead of as copy-paste round-trips. It's idempotent — invoke every time you fire this skill.

Capture the URL it returns. If it returned one, inject it as `window.__CLAUDE_SUBMIT_URL__` in the HTML you're about to write. If it reported web/sandbox mode (no URL returned), generate the HTML *without* `__CLAUDE_SUBMIT_URL__` set — `submitToClaude` will fall back to clipboard mode automatically.

Skipping this step costs the user a copy-paste round-trip on every submit. Invoking the skill is cheap and idempotent.


## When to use this skill

- "Help me tune X" / "Find the right value for Y"
- "Try different settings for Z and let me pick"
- "I'm not sure what value should be / what feels right"
- "Build a playground for X"
- Any time the user is in "I'll know it when I see it" territory

## Output requirements

Real-time updating preview as the user manipulates controls. One Submit button that calls `submitToClaude` with the tuned values — the receiving agent reads the standard envelope and applies them.

Critical: the playground must work without explanation. Sliders should be labeled, ranges should be sensible, defaults should be the user's current values (or reasonable starting points).

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

1. **Title** — what's being tuned, in plain language
2. **Preview area** — the thing the parameters control, prominently shown
3. **Controls** — sliders/dropdowns/toggles for each parameter
4. **Current values display** — show the chosen values as code/data, updating live
5. **Submit button** — one button only. Calls `submitToClaude` with the chosen values in the standard payload envelope. The receiving agent extracts whatever shape it needs (CSS variables, JSON, JS object) from the envelope when responding — no need for parallel "copy as CSS" / "copy as JSON" buttons on the page.
6. **Reset** — back to defaults

## Patterns

### Pattern A: Single-component tuner

One thing on stage (a button, a card, an animation). Every parameter exposed as a control. Live preview front and center. Used for animation tuning, component styling, hover effects.

Layout: stage at top or left, controls grouped at bottom or right. Group related controls under headers ("Timing", "Visual", "Behavior").

### Pattern B: Algorithm parameter explorer

For non-visual parameters (debounce window, retry count, batch size, threshold). The "preview" is a synthetic visualization of what the algorithm does — a chart, a simulated event stream, a metric. Show the resulting behavior, not just the inputs.

### Pattern C: Value picker for text-painful values

Color pickers, easing curve editors, regex testers, cron schedule pickers, crop region selectors. The control IS the preview — manipulate the value visually, see it applied immediately.

### Pattern D: Multi-parameter sweep

For when the user wants to compare a grid of combinations. Lock most values, vary 1–2, see the cross-product. Useful for "how does this look at different sizes" or "what happens at different concurrency levels".

## Control conventions

- **Sliders** — continuous numeric values with sensible min/max. Show current value next to the label.
- **Dropdowns** — discrete options where order doesn't matter
- **Segmented buttons** — discrete options where it's nice to see all at once (e.g., "spring | ease-out | linear")
- **Toggles** — booleans
- **Number inputs** — when the range is large or the user wants to type
- **Color inputs** — `<input type="color">` for color, plus a hex display

Always show the current value as text next to (or under) the control. Numbers without units are confusing — include "ms", "px", "%" labels.

## Submission shape

The envelope's `data` object should carry both the raw values and a short context string so the receiving session knows what to do with them:

```js
submitToClaude({
  skill: 'html-interactive-playground',
  kind:  'tuned-params',
  data: {
    target: 'checkout button hover/press animation',
    params: { duration_ms: 220, scale: 1.04, shadow_px: 8, easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)' },
    note:   'Apply to CheckoutButton.tsx',
  },
  version: 1,
});
```

`target` and `note` give the receiving agent context; `params` is the structured truth. Don't fork this into a separate "copy as prompt" button — the JSON envelope IS the export.

## Anti-patterns

- Sliders with no value displayed. The user can't tell what they picked.
- Defaults that don't match the user's actual current setup. They'll spend the first minute resetting.
- Preview that updates only on button-click. Live updates are the whole point.
- Playgrounds without a Submit button. Without it, the user has to manually transcribe values, which defeats the purpose.

## Example prompt

> Build me a playground for tuning the debounce on our search input. I want to see synthetic keystroke events fire and the resulting query firing pattern. Sliders for debounce ms, leading/trailing edge, max wait. Copy button to send the params back.

Output: HTML file with a synthetic keystroke generator at top, a timeline showing keystrokes vs query fires below, three sliders + two toggles for the debounce parameters, and a Submit-to-Claude button.

Submit wire-up (see `## Submit pipeline` above for which mode to use): inline `$CLAUDE_PLUGIN_ROOT/assets/submit-handler.js`, then call:
```js
submitToClaude({
  skill: 'html-interactive-playground',
  kind: 'tuned-params',
  data: {
    target: 'search-input debounce',
    params: { debounce_ms: 220, leading: false, trailing: true, max_wait_ms: 800 },
    note:   'Apply to SearchInput.tsx',
  },
  version: 1,
});
```
