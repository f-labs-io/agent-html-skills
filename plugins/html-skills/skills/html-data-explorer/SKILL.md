---
name: html-data-explorer
description: Build HTML data explorers for CSV, JSON, log, and event data — filterable tables, faceted search, inline charts, timeline scrubbing, A/B test result dashboards. Use whenever the user has a dataset to explore, browse, filter, chart, facet, or analyze — especially for ad-hoc analysis where opening a heavy BI tool is overkill. Reach for this when the user pastes data, mentions a CSV/JSON/log file, or asks to "look at" or "analyze" a dataset.
---

# HTML Data Explorer

For ad-hoc data exploration — a CSV someone pasted, a JSON dump from an API, a log file from production — opening Tableau or even a Jupyter notebook is overkill. A self-contained HTML file with the data baked in, a filterable table, a few charts, and faceted search is faster to build and faster to share.

## When to use this skill

- "Look at / analyze / explore this CSV / JSON / log data"
- "Show me [a chart, filter, breakdown] of this data"
- "Build me a quick dashboard for X"
- "Help me find the rows where Y"
- Pasted tabular data with an implicit "do something useful with this"
- Log files where the question is "what happened around time T"

## Output requirements

Data baked into the file as a JS object/array — no separate file to load, no fetch call. Filtering and charting happens entirely in the browser. Pre-aggregated views update live as filters apply.

If the dataset is large enough that inlining is awkward (>~5MB), still inline it but warn the user about file size; otherwise the artifact loses its "just send the link" superpower.

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

1. **Header** — what dataset this is, row count, time range covered (if temporal)
2. **Filter bar** — facets/filters that narrow the data
3. **Summary panel** — counts and aggregates that update as filters apply
4. **Main view** — table, chart, or both (often both)
5. **Detail drawer** — click a row to see the full record
6. **Export** — copy filtered subset, copy a SQL-like predicate, etc.

## Patterns

### Pattern A: Filterable table

For tabular data where the user wants to find rows matching criteria. Sortable columns, search, multi-select filters per column. Row count visible at all times. Click row to expand.

Pagination when >~500 rows. Virtualization (e.g., visible-only rendering) when >5000.

### Pattern B: Faceted search

For data with categorical fields. Sidebar of facets, each showing counts for each value. Click to filter. Multiple facets compose (AND across facets, OR within a facet).

### Pattern C: Time-series viewer

For temporal data (logs, metrics, events). Timeline at the top, brushable to zoom. Aggregated chart for the selected window. Detail table below showing events in the window. Useful for "what happened around time T".

### Pattern D: A/B test dashboard

For experiment results. Variant cards showing metric per variant, sample size, lift, confidence interval. Cohort breakdowns. Color confidence by significance.

### Pattern E: Inline chart explorer

For "show me a chart of X by Y". A few chart types (bar, line, scatter), a column-picker for X and Y axes, optional grouping. Charts update as the user changes the picks.

## Charts — keep it simple

Don't pull in a heavy charting library if you don't need to. For small datasets, hand-rolled SVG charts are fine and load instantly.

When a library is genuinely needed, inline it via a CDN link. Reasonable choices:
- **Chart.js** for standard charts (bar, line, scatter)
- **Recharts** if the artifact is React-based
- **D3** for custom or complex visualizations

Avoid: Plotly (too heavy for ad-hoc), enterprise BI libs (overkill).

## Filter UX

- Filters update results live — no "Apply" button
- Show active filter count near the filter bar
- Always visible "Clear all filters" button
- Persist filter state in URL hash so the user can bookmark/share a specific view

## Export

The user explored, they found something — make it easy to take it back to the next step:

- **Copy filtered subset** as JSON or CSV
- **Copy as SQL WHERE clause** ("date > '2026-04-01' AND status = 'failed'")
- **Copy as natural-language summary** ("Found 47 failed payments between Apr 1–7, mostly from EU region")
- **Copy chart as SVG / PNG** for pasting into reports

## Anti-patterns

- Loading data from a separate file. Defeats the "send the link" property.
- Filtering that requires an Apply button. Live filtering is the whole point.
- Forgetting the row count. The first thing a data person wants to know.
- Silent truncation of large datasets. Tell the user explicitly: "showing first 500 of 12,408 rows".
- Charts without axis labels or units. Useless to anyone but the builder.

## Example prompt

> Here's our payment failure log for last week [pasted CSV, 4000 rows]. Build me an HTML explorer — filters by region, error code, processor, and time range. A timeline chart at top showing failures per hour. Table below with click-to-expand details. Copy-as-SQL button.

Output: HTML file with the 4000 rows baked in, a filter bar (4 facets), a timeline chart at top with brushable selection, filterable/sortable table below, click-to-expand row detail, summary stats at top updating with filters, and a copy-as-SQL button.
