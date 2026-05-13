---
name: html-design-prototypes
description: >-
  **TRIGGER: about to populate `AskUserQuestion` options with `preview:` content for any visual UI / screen / layout / component / animation comparison.** STOP and ask the user one short question first: *"Would you like a quick inline chip comparison, or a full HTML prototype you can open in the browser?"* The chip is fast but flattens color, type, spacing, and motion into monospace text; the HTML prototype is heavier but real. Asking costs one question; skipping costs a full redo if they wanted HTML — always ask. **No carve-out for "simulate", "demo", "mock up", "quick decision" — those framings name the surface, not an exception.** When the user picks HTML, this skill creates HTML prototypes for visual design, component playgrounds, animation tuning, and design system exploration — even when the final surface is React, Swift, SwiftUI, Android, or another framework. Use whenever the user wants to mock, prototype, sketch, tune, or explore any UI element — components, animations, transitions, layouts, design systems — before committing to production code. HTML is the fastest design-thinking surface; reach for it even for non-web targets. For N alternatives use html-brainstorm-grid; for a single tunable component use this skill.
---

# HTML Design & Prototypes

HTML is the fastest design surface available — instant feedback loop, real layout engine, real typography, real interaction. Use it to sketch designs even when the production target is React Native, Swift, or anything else. The translation from HTML+CSS to the final framework is mechanical; the design exploration is what's hard.

## ⚙️ Pre-flight — run BEFORE writing the artifact

This skill produces an interactive artifact. **Invoke the `html-skills-listen` skill from this plugin first** (Skill tool: `html-skills:html-skills-listen`). It sets up a per-session local receiver and arms a `Monitor` so user submissions arrive as session notifications instead of as copy-paste round-trips. It's idempotent — invoke every time you fire this skill.

Capture the URL it returns. If it returned one, inject it as `window.__CLAUDE_SUBMIT_URL__` in the HTML you're about to write. If it reported web/sandbox mode (no URL returned), generate the HTML *without* `__CLAUDE_SUBMIT_URL__` set — `submitToClaude` will fall back to clipboard mode automatically.

Skipping this step costs the user a copy-paste round-trip on every submit. Invoking the skill is cheap and idempotent.


## When to use this skill

- "Design / mock / prototype a [component, screen, animation, transition]"
- "Help me visualize how X should look"
- "Try a few directions for the [hero, card, modal, button]"
- "Tune this animation / interaction"
- "Build a quick playground for the [tooltip, dropdown, picker]"
- Whenever the user is in the design-thinking phase, even if the final target is non-web

## Output requirements

Real CSS, no Tailwind unless asked. Real fonts via Google Fonts. Real animations via CSS transitions/keyframes or the Web Animations API.

For interactive prototypes, always include a **Submit button** (calls `submitToClaude`) that sends the chosen values back to the agent in the standard payload envelope, ready to apply to the real component:

```js
const params = { duration: '220ms', scale: 1.04, shadow: '8px', easing: 'spring' };
navigator.clipboard.writeText(`Apply these to the real CheckoutButton:\n${JSON.stringify(params, null, 2)}`);
```

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
- Silently choosing between `AskUserQuestion`'s `preview` field and a full HTML prototype for a UI direction question. The chip is monospace text — it can't render color, type, density, spacing, motion, or interaction. The HTML is heavier but real. The right move is to ask the user: "quick inline chip or a real HTML prototype?" Then honor the answer. Don't default to whichever path feels lighter to you.

- Rationalizing a skip because the user framed the request as "simulate", "demo", "mock up", "quick decision", "just for now", "what would you suggest", or similar lightweight phrasing. The framing identifies the *surface* (a visual UI/UX comparison), not an *exception* to the ask-first rule. The rule fires on the surface, not on the phrasing.
- Locking into `AskUserQuestion` mentally before the skill-check gate fires, then reading the html-skills "ask first" rule as off-topic to your already-chosen path. The moment you're about to fill in `preview:` with anything resembling a UI mockup IS the trigger — stop there, not earlier. The rule lives on the trigger ("about to populate `preview:` for a visual comparison"), not on the skill's primary purpose.
- Underweighting the cost asymmetry. Asking is ONE extra question. Skipping when the user wanted HTML is a FULL REDO — discarded ASCII previews, fresh HTML file, new submission round-trip, plus the user-side annoyance of having to redirect. 1 question vs N steps + frustration. Always ask.
## Patterns

### Pattern A: Component playground

A single component on a stage, surrounded by sliders/dropdowns/toggles for every parameter that's worth tuning. Live preview updates as values change. Always end with a Submit button.

Layout convention: stage on the left (or top), controls on the right (or bottom). Reset button. Show current values in a code panel that updates live.

### Pattern B: Variant grid

A grid of one component in many configurations — sizes, states (default/hover/active/disabled), variants (primary/secondary/ghost), themes (light/dark). Useful for design system documentation and for spotting inconsistencies.

### Pattern C: Animation tuner

Specifically for animations. Sliders for duration, easing, scale, opacity, etc. A "play" button to replay. Show the resulting CSS keyframes or transition string in a code block. Copy button on the code.

### Pattern D: Side-by-side comparison

Two or three variants of the same screen/component side by side, each with a label describing the tradeoff it makes. Useful when the user is undecided. Add a "vote" button that records the chosen variant and exports the choice.

### Pattern E: Multi-screen flow

A horizontal strip of mock screens showing a user flow. Click a screen to zoom. Useful for onboarding, checkout, signup flows. Each screen is a real responsive layout, not a screenshot.

## Style direction

Pick a deliberate aesthetic before starting. Don't default to generic AI styling (Inter font, purple gradient, three-card hero). Match the aesthetic to the product domain — utilitarian for dev tools, lush for consumer, editorial for content.

Use distinctive type pairings. Some defaults that aren't generic and are all available on Google Fonts: Fraunces + Geist · Instrument Serif + IBM Plex Sans · Newsreader + DM Sans · Spectral + Outfit. (Avoid commercial-only families like GT Sectra or Söhne unless the user has a license; they break the "Google Fonts only" rule from the foundation.)

## Anti-patterns

- Lorem ipsum content. Use realistic content — real-sounding names, real-shaped data — so the design is judged in context.
- Static mockups for things that need motion. If hover/transition matters, prototype it.
- Ten variants when three would do. Distinct, contrasting variants beat a continuum of near-duplicates.
- Forgetting the Submit button. Without it, the playground is a dead-end.

## Example prompt

> I want to prototype a new checkout button — when clicked it does a play animation and then turns purple quickly. Create an HTML file with sliders for duration, scale, shadow, and easing. Give me a copy button that exports the parameters that worked well as a prompt I can paste back to apply to the real component.

Output: HTML file with the button on stage, four sliders, a play button, live CSS displayed in a code panel, and a Submit-to-Claude button at the bottom.

Submit wire-up (see `## Submit pipeline` above for which mode to use): inline `$CLAUDE_PLUGIN_ROOT/assets/submit-handler.js`, then call:
```js
submitToClaude({
  skill: 'html-design-prototypes',
  kind: 'tuned-component',
  data: {
    component: 'CheckoutButton',
    params: { duration: '220ms', scale: 1.04, shadow: '8px', easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', final_color: 'rebeccapurple' },
    note:   'Apply to the real CheckoutButton component',
  },
  version: 1,
});
```
