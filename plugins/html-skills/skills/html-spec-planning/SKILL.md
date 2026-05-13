---
name: html-spec-planning
description: Create rich HTML documents for project specs, implementation plans, design exploration, RFCs, and brainstorming. Use whenever the user asks for a spec, plan, RFC, design doc, brainstorm, or wants to explore approaches/options/alternatives — even when they don't explicitly say "HTML". Strongly prefer HTML over markdown for any planning artifact longer than a screen, especially when the artifact will be shared with reviewers or fed back to the agent for implementation.
---

# HTML Spec, Planning & Exploration

Use HTML as the working surface for thinking through problems — brainstorms, alternative explorations, mockups, and implementation plans. Markdown specs over ~100 lines stop getting read; HTML specs get read because they're navigable, visual, and shareable as a link.

## When to use this skill

- "Write a spec / RFC / design doc / proposal for X"
- "I'm not sure how to approach X — explore the options"
- "Make me an implementation plan for X"
- "Brainstorm approaches to X"
- "Lay out the tradeoffs for X"
- Whenever the planning artifact will be reviewed by humans, or later read by another Claude session for implementation

## Output requirements

Save with a descriptive filename like `<topic>-spec.html` or `<topic>-plan.html` so multiple planning artifacts on one project compose into a readable folder rather than colliding on `output.html`.

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

A planning artifact has predictable sections. Use them or a deliberate variation:

1. **Title + one-sentence framing** — what this document is and isn't
2. **Context / problem** — what we're trying to solve, who cares
3. **Constraints** — non-negotiables, scope boundaries
4. **Approach(es)** — either one chosen direction or a comparison of N
5. **Mockups / diagrams** — visuals for any spatial or relational concept
6. **Data flow / sequence** — if relevant, an SVG or HTML+CSS diagram
7. **Implementation plan** — concrete steps, files to touch, code snippets
8. **Open questions** — things the writer doesn't know yet, surfaced not buried
9. **Out of scope** — explicit "we are not solving X here" list

Not every doc needs every section. A pure brainstorm may stop at section 4. An implementation plan starts at section 7.

## Patterns

### Pattern A: Single-direction spec

When the direction is decided. Lead with the chosen approach, justify briefly, then go deep on implementation. Mockups inline. Code snippets in `<pre>` with syntax highlighting via a tiny inline highlighter or copy-pasted from a tokenizer.

### Pattern B: N-way exploration

When the direction isn't decided. Lay out 3–6 distinct approaches in a grid. Each card has: name, sketch, +pros, −cons, "best when…". End with a recommendation section if asked, or leave the choice open.

### Pattern C: Multi-file web

For larger problems, produce several linked HTML files: `01-context.html`, `02-options.html`, `03-chosen-approach.html`, `04-implementation.html`. Cross-link them with `<a href>`. A reviewer or a follow-up Claude session can then pull all of them in for broader context, instead of one giant doc nobody reads end-to-end.

## Anti-patterns

- Generic AI aesthetic (purple gradients, Inter font, centered hero with three feature cards). Pick a clear visual direction matched to the document's tone.
- Decorative mockups that don't carry information. Every visual should add something prose can't say efficiently.
- Burying open questions in a long flat doc. Surface them visually — a sidebar, a banner, a colored callout.
- Code snippets as screenshots. Use real `<pre><code>` so they can be copied.

## Example prompt

> Create a spec in HTML for adding offline sync to our notes app. Cover the conflict resolution strategy, give me 3 alternatives with tradeoffs, sketch the data flow, and end with an implementation plan I can hand to another session.

Output: one HTML file with sections for context, three approach cards, an SVG sync-flow diagram, an implementation plan with file-by-file steps, and an "open questions" callout. Save as `offline-sync-spec.html`.
