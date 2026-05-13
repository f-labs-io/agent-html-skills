---
name: html-comparison-matrix
description: >-
  **TRIGGER: about to populate `AskUserQuestion` options with `preview:` content for any comparison heavier than 2-3 short text labels (>2 axes or >3 candidates, or weighted/scored).** STOP and ask the user one short question first: *"Would you like a quick inline chip per option, or a full HTML matrix with weighted columns and live re-ranking?"* The chip is one tool call but loses all structure (no table, no weights, no sorting, no live recompute); the matrix is heavier but preserves the structure the comparison needs. Asking costs one question; skipping costs a full redo. **No carve-out for "simulate", "demo", "quick decision" — the framing names the surface, not an exception.** When the user picks HTML, this skill generates sortable, weighted HTML scoring matrices for evaluating named candidates — for the EVALUATIVE phase of comparison, when 2+ specific candidates ARE named in the prompt. Use when the user names options and asks to compare, evaluate, score, or pick between them: "compare X, Y, Z", "should we use A or B", "evaluate these libraries", "pick between [list]", "build vs buy", "which of these X should we choose". Make weights live-adjustable so totals update in real time. If the user is still GENERATING candidates rather than choosing among named ones ("brainstorm options", "show me approaches", "what are the ways"), hand off to html-brainstorm-grid instead — that skill handles the generative phase.
---

# HTML Comparison Matrix

When picking between candidates on multiple criteria, a comparison matrix beats a paragraph. A weighted matrix beats an unweighted one — weights surface the implicit priorities and let the user argue with their own past judgments.

> **Phase boundary.** This skill handles the *evaluative* phase of comparison — scoring candidates that already exist. If the user hasn't named candidates yet and is still asking "what are the options" or "show me approaches", hand off to `html-brainstorm-grid` instead. The boundary signal is whether candidates appear in the prompt: if so, score them here; if not, generate them there. The two skills are designed to compose — generate options there, then evaluate them here.

## ⚙️ Pre-flight — run BEFORE writing the artifact

This skill produces an interactive artifact. **Invoke the `html-skills-listen` skill from this plugin first** (Skill tool: `html-skills:html-skills-listen`). It sets up a per-session local receiver and arms a `Monitor` so user submissions arrive as session notifications instead of as copy-paste round-trips. It's idempotent — invoke every time you fire this skill.

Capture the URL it returns. If it returned one, inject it as `window.__CLAUDE_SUBMIT_URL__` in the HTML you're about to write. If it reported web/sandbox mode (no URL returned), generate the HTML *without* `__CLAUDE_SUBMIT_URL__` set — `submitToClaude` will fall back to clipboard mode automatically.

Skipping this step costs the user a copy-paste round-trip on every submit. Invoking the skill is cheap and idempotent.


## When to use this skill

- "Compare X, Y, and Z" (libraries, vendors, frameworks, designs)
- "Which [tool, library, vendor, approach] should we use?"
- "Help me decide between A and B"
- "Evaluate [X] against [Y, Z]"
- Build-vs-buy decisions
- Anything with multiple **named** candidates and multiple selection criteria

## When NOT to use this skill

- The user is asking the skill to generate options ("brainstorm approaches", "show me ways"). Use `html-brainstorm-grid`.
- Only one candidate is named — no comparison to make. Use `html-spec-planning` to write up the rationale.
- The "comparison" is two paragraphs that don't need a weighted scoring system. A simple side-by-side in prose is fine.

## Output requirements

The artifact has:
- A matrix of candidates × criteria
- Per-criterion weight sliders that update totals live
- Per-candidate score breakdowns
- A clear "verdict" pane that updates as weights change
- Export of the configured matrix and current verdict as JSON or markdown

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
- Silently choosing between `AskUserQuestion`'s `preview` field and a full HTML matrix for a multi-axis comparison. The chip is plain text — no table, no weighted columns, no sort controls, no live recompute. The matrix is heavier but preserves the structure. When the comparison has >2 axes or >3 candidates, ask the user first: "quick inline chip or full HTML matrix?" Then honor the answer.

- Rationalizing a skip because the user framed the request as "simulate", "demo", "mock up", "quick decision", "just for now", "what would you suggest", or similar lightweight phrasing. The framing identifies the *surface* (a visual UI/UX comparison), not an *exception* to the ask-first rule. The rule fires on the surface, not on the phrasing.
- Locking into `AskUserQuestion` mentally before the skill-check gate fires, then reading the html-skills "ask first" rule as off-topic to your already-chosen path. The moment you're about to fill in `preview:` with anything resembling a UI mockup IS the trigger — stop there, not earlier. The rule lives on the trigger ("about to populate `preview:` for a visual comparison"), not on the skill's primary purpose.
- Underweighting the cost asymmetry. Asking is ONE extra question. Skipping when the user wanted HTML is a FULL REDO — discarded ASCII previews, fresh HTML file, new submission round-trip, plus the user-side annoyance of having to redirect. 1 question vs N steps + frustration. Always ask.
## Core structure

```
              Criterion A  Criterion B  Criterion C  …  Total
              weight:0.4   weight:0.3   weight:0.3
Candidate 1      8/10         6/10         9/10        7.5
Candidate 2      6/10         9/10         5/10        6.6
Candidate 3      7/10         7/10         8/10        7.3
```

The matrix is the artifact. Layout: candidates as rows, criteria as columns. Score cells. A "Total" column on the right. Weight controls in the column headers.

## Scoring schemes

Pick one and apply consistently:

- **0–10 scale** — most flexible, most interpretable
- **0–5 stars** — fewer levels, less hair-splitting
- **Tiered (poor/ok/good/great)** — semantic, harder to total
- **Pass/fail per criterion** — for hard requirements (must-haves)

Mix is fine: some criteria as pass/fail (a "must support TypeScript"), others as scored. Pass/fail criteria short-circuit — fail any and the candidate is out.

## Weight controls

Sliders or numeric inputs in each column header, summing to 1.0 (normalize automatically when the user adjusts one). As the user moves a weight, totals re-compute live and rows re-sort if sorted by total.

Show each weight visibly: "Performance · 35%". Use color or thickness to make the heaviest criteria visually obvious.

## Cell content

Score number is the main signal, but each cell should also have:
- **Tooltip / expand** showing the rationale for the score
- **Source link** if the score came from a benchmark, doc, or test

The rationale is what makes the matrix defensible. A score of "7" with no explanation is worth less than a score of "6" with "fastest of the three on cold-start; loses on warm-call".

## Verdict pane

A panel that explains the current weighting and what it implies. Updates as the user changes weights:

> With current weights (Performance 40%, DX 30%, Maintenance 30%): **Candidate 2 wins (7.8 vs 7.3 vs 6.9).** Note: Candidate 2 fails the "supports SSR" hard requirement. Recommend reconsidering or relaxing the requirement.

If a hard requirement fails, surface that prominently. Don't let the user pick a candidate that's literally disqualified.

## Patterns

### Pattern A: Library evaluation
Candidates: 3–5 libraries. Criteria: bundle size, performance, DX, maintenance status, ecosystem, license. Weights vary by project.

### Pattern B: Vendor selection
Candidates: 2–4 vendors. Criteria: price, feature coverage, support quality, integration cost, SLA, security posture. Often includes pass/fail for compliance requirements.

### Pattern C: Architectural pattern comparison
Candidates: approaches (monolith / split / event-driven / etc.). Criteria: time to ship, ops cost, scaling characteristics, team familiarity, future flexibility. More qualitative; tooltips matter.

### Pattern D: Design pattern selection (within code)
Candidates: implementation approaches for one specific problem. Criteria: complexity, perf, testability, alignment with existing code, learning curve.

## Sensitivity check

Optionally include a "what would have to change" panel: "Candidate 2 wins if Performance ≥ 35%. To make Candidate 1 win, Maintenance weight needs to exceed 50%." Helps the user see how robust the verdict is.

## Anti-patterns

- Scores without rationale. Becomes "trust me bro" math.
- Weights that don't sum to 1. Math gets confusing.
- Unweighted matrices for important decisions. Implicit weights are still weights — make them explicit.
- Inflating scores to make the chosen winner win. Be honest; if the matrix says wrong, change the weights or the criteria, not the scores.
- Hiding hard-requirement failures. Disqualifications must be visible.

## Example prompt

> Help me pick between three feature flag libraries: LaunchDarkly, Unleash, and Flagsmith. Criteria: price, on-prem support, SDK ecosystem, dev experience, observability. Hard requirement: must support our existing Python and TypeScript stack. Build me an HTML matrix with adjustable weights.

Output: HTML file with the three candidates as rows, five criteria as columns with weight sliders, scored cells with tooltips for rationale, a "must support Python+TS" pass/fail row, a verdict pane showing the current winner with sensitivity notes, and a Submit-to-Claude button.

Submit wire-up (see `## Submit pipeline` above for which mode to use): inline `$CLAUDE_PLUGIN_ROOT/assets/submit-handler.js`, then call:
```js
submitToClaude({
  skill: 'html-comparison-matrix',
  kind: 'matrix-verdict',
  data: {
    candidates: ['LaunchDarkly', 'Unleash', 'Flagsmith'],
    criteria:   ['price', 'on-prem', 'sdk-ecosystem', 'dx', 'observability'],
    weights:    { price: 0.25, 'on-prem': 0.25, 'sdk-ecosystem': 0.2, dx: 0.15, observability: 0.15 },
    scores:     { LaunchDarkly: { price: 5, 'on-prem': 3, /* ... */ }, /* ... */ },
    hard_reqs:  { 'python+ts': { LaunchDarkly: true, Unleash: true, Flagsmith: true } },
    winner:     'Unleash',
    rationale:  '<optional user text>',
  },
  version: 1,
});
```
