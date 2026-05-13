---
name: html-research-reports
description: Synthesize multi-source research (codebase, git history, Slack, web, MCPs) into readable HTML reports — concept explainers, weekly status reports, incident reports, technical deep-dives, learning artifacts. Use whenever the user wants a write-up, explainer, summary, deep-dive, status report, retrospective, or report that pulls from multiple sources — especially when they mention sharing it with someone else, or when the topic involves understanding rather than implementing. Strongly prefer this over markdown for any report longer than a screen.
---

# HTML Research, Reports & Learning

HTML reports get read; markdown reports of the same length don't. Use HTML whenever the goal is for a human (often someone other than the user) to actually absorb information — concept explainers, status reports, incident reports, knowledge transfer.

## When to use this skill

- "Summarize how X works"
- "Explain the Y system to me / to my team / to leadership"
- "Write up the incident from yesterday"
- "Weekly status update for my manager"
- "I want to learn about X — synthesize from the codebase + git history + web"
- "Prepare a technical brief on Z"
- Any time the goal is comprehension or sharing, not implementation

## Output requirements

Designed for one-time reading — optimize for the reader who opens it once, gets what they need, closes it. Navigable by scrolling and, for longer reports, a sticky sidebar TOC or tab strip.

Include:
- Title + one-sentence framing
- A source list at the bottom — what was synthesized to produce this (files, commits, threads, URLs). Concrete enough that a reader can verify a claim without asking.

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

Adapt to the report type, but the spine is usually:

1. **TL;DR** — what someone who reads only the first screen needs
2. **Context** — why this matters now
3. **Main content** — the substance, broken into navigable sections
4. **Diagrams** — SVG or HTML+CSS for any spatial/sequential concept
5. **Annotated code/data snippets** — when relevant
6. **Gotchas / surprises** — things that aren't obvious
7. **What's next / open questions / follow-ups** — the action edge
8. **Sources** — what was synthesized to produce this

## Patterns

### Pattern A: Concept explainer

For "explain how X works". Lead with a flow diagram of the concept. Annotate the 3–5 key code snippets inline. End with a "gotchas" section listing the non-obvious behaviors. Optimize for someone reading it once.

### Pattern B: Weekly status report

For "summarize what I/we shipped this week". Section by area or by project. Include numbers (PRs merged, incidents, deploys) when available. End with a "next week" preview. Keep it scannable — a busy reader should be able to read just the section headers and bold sentences and get the picture.

### Pattern C: Incident report

For postmortems. Sections: summary, timeline, root cause, what went well, what didn't, action items. Include a visual timeline (SVG or HTML grid) of the incident. Severity-tag action items by impact. Don't sandbag — name the actual problem.

### Pattern D: Technical deep-dive

For learning artifacts. Long-form, ~5–10 sections, with a sticky sidebar TOC. Mix prose, diagrams, and annotated code. End with "further reading" pointing to original sources.

### Pattern E: Decision memo

For "should we do X" reports. Sections: problem, options, recommendation, risks, what we'd need to commit to. Lead with the recommendation, justify it, then go into the alternatives. Don't bury the lede.

## Synthesizing across sources

When given access to MCPs (Slack, Linear, git, web), pull from all of them and cite inline. Cite as "(commit a3f4)", "(Slack: #incidents, Tue)", "(Linear: ENG-1247)" — concrete enough that the reader can verify, not so verbose it clutters the prose.

## Anti-patterns

- Restating what's already in the linked sources. Synthesize, don't paraphrase.
- "Engagement bait" structure — a long preamble before getting to the point.
- Hedging on every claim. If the synthesis points one way, say so.
- Missing the action edge. Reports that don't end in "so what" don't get acted on.

## Example prompt

> I don't understand how our rate limiter actually works. Read the relevant code and produce a single HTML explainer page: a diagram of the token-bucket flow, the 3–4 key code snippets annotated, and a "gotchas" section at the bottom. Optimize it for someone reading it once.

Output: HTML file with a token-bucket SVG flow diagram up top, four annotated code snippets in the middle, three gotchas at the bottom. Source list cites the specific files read.
