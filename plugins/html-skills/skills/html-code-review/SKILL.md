---
name: html-code-review
description: Generate HTML artifacts for code review, PR explanation, and codebase understanding — rendered diffs with inline annotations, severity-coded findings, refactor risk maps, before/after migration views, and subsystem walkthroughs. Use whenever the user wants to review, explain, or understand a PR, refactor, codebase area, or subsystem — especially before merging, when onboarding others to a change, or when the GitHub diff view doesn't show enough context. Default to attaching an HTML explainer to every non-trivial PR.
---

# HTML Code Review & Understanding

The default GitHub diff view is fine for tiny PRs and useless for anything that touches multiple files, has subtle ordering, or involves a refactor. HTML lets you render the actual diff with margin annotations, severity tags, flowcharts of what changed, and risk maps showing which areas to look at hardest.

## When to use this skill

- "Review this PR / explain this change / write up this refactor"
- "I just made a change to X — generate an explainer to attach to the PR"
- "Help someone unfamiliar with X understand this code"
- "Walk me through how Y works in this codebase"
- "Map the risk of this refactor"
- Before merging any PR that touches more than one subsystem, has subtle ordering effects, or that a non-author needs to understand

## Output requirements

Render diffs as real HTML so reviewers can copy lines. Use a monospace font for code and a readable serif or sans for prose. Reviewers will open this on a phone during a commute, so the responsive collapse from the foundation block is load-bearing here.

Include a header with: PR title, author, branch, and a one-sentence summary. End with a "what to look at hardest" section that ranks the diff by reviewer attention required.

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

## Core structure

1. **Header** — PR identity, branch, summary, status pills
2. **TL;DR** — 2–3 sentences a non-author can understand
3. **What changed, why** — the narrative, not a file list
4. **Risk map** — visual showing which files/areas are hot vs safe
5. **Annotated diffs** — the actual code with margin notes
6. **Concept callouts** — for the parts that benefit from explanation outside the diff
7. **Test coverage** — what's tested, what isn't, why
8. **Reviewer checklist** — what you specifically want eyes on

## Patterns

### Pattern A: PR explainer (attach-to-PR)

Compact (~5 sections, ~1 screen of TL;DR + risk map at top). Diffs come second. Designed for a reviewer who has 10 minutes. Color findings by severity:

- **🔴 blocking** — must address before merge
- **🟡 nit** — author's choice
- **🟢 nice** — observation, no action needed

### Pattern B: Refactor risk map

For larger refactors. The top of the page is a visual map of files/modules colored by how much they changed and how exposed they are. Click a hot zone to jump to the annotated diff for that area. Include a "if I had 30 minutes, look at…" prioritized list.

### Pattern C: Subsystem tour

When the goal is teaching, not reviewing. Less diff-heavy, more explanation-heavy. Start with a flow diagram of how the subsystem works, then the 3–5 key files annotated, then a "gotchas" section at the bottom.

### Pattern D: Migration before/after

For migrations (DB schema, API version, framework upgrade). Side-by-side before/after at multiple zoom levels: high-level architecture at the top, then per-file diffs, then per-line for the critical bits.

## Annotation style

Inline annotations sit in the right margin next to the diff line(s) they reference. Use a thin connecting line or color-matched dot to anchor them. Keep each annotation under ~40 words — link out for longer context.

Don't bury concerns in prose paragraphs that come after the diff. Put them next to the line.

## Anti-patterns

- Re-stating the diff in prose. The diff is already there.
- Annotations longer than the code they annotate. Link out instead.
- A wall of green checkmarks. Reviewers stop reading those by the third one.
- Pretending you reviewed parts you didn't. Mark sections as "skipped" honestly.

## Example prompt

> Help me review this PR by creating an HTML artifact that describes it. I'm not very familiar with the streaming/backpressure logic, so focus on that. Render the diff with inline margin annotations, color-code findings by severity, and put a risk map at the top.

Output: HTML file with a top-of-page risk map (streaming layer marked red, everything else green), TL;DR, narrative, then full annotated diffs of the streaming files with severity-tagged margin notes, ending with a 5-item reviewer checklist.
