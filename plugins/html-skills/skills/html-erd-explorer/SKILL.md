---
name: html-erd-explorer
description: Generate HTML entity-relationship diagrams (ERDs) and database schema visualizations with clickable tables, relationship paths, and migration before/after views. Use whenever the user has a database schema, data model, or table structure to document, explain, migrate, or explore — even when they call it a "data model", "schema diagram", or just "the tables". Reach for this any time the conversation touches database structure with more than ~3 tables.
---

# HTML ERD & Schema Explorer

Database schemas are inherently visual — tables connected by foreign keys, with cardinality and direction. ERDs in markdown are awkward; in dedicated tools they're heavy. An HTML ERD is portable, embeddable in a doc, and click-to-explore.

## When to use this skill

- "Diagram our [schema, data model, database, tables]"
- "Show me how [table X] relates to [table Y]"
- "Document the schema for [feature/service]"
- "Plan the migration from this schema to that one"
- "Explain how a query touches the schema"
- Any time a database structure with ≥3 tables enters the conversation

## Output requirements

Tables rendered as cards/boxes with their columns listed. Foreign key relationships drawn as connecting lines with cardinality markers (1, *, etc.). Click a table to expand or focus.

Include a legend explaining symbols (PK, FK, indices, nullable).

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

## Core ERD components

### Table card

```
┌─────────────────────────────┐
│ users                       │
├─────────────────────────────┤
│ 🔑 id          uuid         │
│    email       text  unique │
│    created_at  timestamptz  │
│    org_id      uuid → orgs  │
└─────────────────────────────┘
```

Each card shows:
- Table name (header)
- Columns: name, type, key markers (PK/FK), nullability, indices
- Optional: row count estimate, table-level comments

### Relationship lines

- **Solid line** = foreign key
- **Cardinality markers** at each end (1, *, 0..1, 1..*)
- **Crow's-foot notation** preferred over text labels for cardinality
- **Color or style** to distinguish strong (cascading) from weak (set null) relationships

### Conventions

- Tables aligned on a grid; primary tables larger or central
- Foreign keys point in the direction of the reference (child → parent)
- Junction tables in many-to-many relationships drawn smaller, between the two main tables

## Patterns

### Pattern A: Full schema overview

All tables in the schema laid out. Useful for new-team-member onboarding. Group tables by domain (auth, billing, content). Include a sidebar list for navigation.

### Pattern B: Subschema deep-dive

A focused view of 3–8 tables related to one feature. More detail per table (every column shown, types and constraints). Cross-references to tables outside the subschema shown as faded "context" cards.

### Pattern C: Migration before/after

Side-by-side or top-bottom: current schema on one side, target schema on the other. Diff annotations: added tables in green, removed in red, changed in amber. Migration steps listed below.

For complex migrations, support a "show intermediate state" toggle that displays the in-flight schema (e.g., during a column rename with a temporary new column).

### Pattern D: Query path explainer

Take a specific query (or a query pattern), highlight the tables it touches, the joins it makes, and the indexes it uses. Useful for explaining slow queries or for query optimization reviews.

### Pattern E: Data lineage view

Show where data flows between tables — typically for analytics/warehouse schemas. Source tables, transformation steps, materialized views, downstream tables. Direction = data movement.

## Layout strategies

ERDs look bad when auto-laid-out badly. For ≤8 tables, hand-position them. For more, group by domain and lay out by group.

- **Star** — one central table (e.g., `users` or `orders`) surrounded by satellites
- **Flow** — left-to-right by lifecycle (e.g., `cart → orders → invoices → payments`)
- **Layered** — top-to-bottom by abstraction (entities at top, junctions middle, transactional at bottom)

If the layout starts looking like spaghetti, the schema probably is — note it, don't hide it.

## Interaction

For schemas larger than ~10 tables, add interaction:

- **Click a table** to highlight all its relationships, fade everything else
- **Hover an FK column** to draw the line clearly
- **Search box** to find a table by name
- **"Show only tables related to X"** filter to focus on a feature

For migration views:
- **Toggle** between current / target / diff
- **Click a changed column** to see the rationale or migration step

## Anti-patterns

- ERDs that omit column types. Half the value is the types.
- Crossing relationship lines that could be untangled by repositioning. Move the boxes.
- Generic "boxes and lines" with no visual distinction between strong and weak FKs.
- Skipping junction tables in M:N. They exist; show them.
- Migration diagrams that show only the new state. The diff is what's interesting.

## Example prompt

> Document our orders schema as an HTML ERD. Tables: users, orders, order_items, products, payments, refunds. Show columns, types, FKs, and primary keys. Group by domain.

Output: HTML file with six table cards laid out by domain (users in one group, products in another, orders/order_items/payments/refunds as the order-flow group), FKs drawn with crow's-foot cardinality, click-table-to-focus interaction, legend in the corner.
