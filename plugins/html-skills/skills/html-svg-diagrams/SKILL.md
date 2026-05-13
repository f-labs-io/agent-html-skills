---
name: html-svg-diagrams
description: Create SVG-based technical diagrams inside HTML — flowcharts, sequence diagrams, state machines, data-flow diagrams, dependency graphs, request/response timelines. Use whenever the user wants to visualize, illustrate, diagram, or sketch a technical concept, system, or process. Strongly prefer SVG over ASCII art, mermaid blocks, or markdown text for anything spatial or relational. Reach for this whenever an explanation involves arrows, boxes, layers, or sequencing — even when the user doesn't say "diagram".
---

# HTML SVG Diagrams & Flowcharts

ASCII diagrams in markdown are a workaround for not having SVG. With SVG inside HTML, you get real shapes, real arrows, real typography, and real positioning — for the same conceptual cost.

Use this skill any time the explanation has arrows, boxes, layers, time, or position. Most technical concepts do.

## When to use this skill

- "Diagram / illustrate / visualize / draw X"
- "Show me how the [request, data, message] flows"
- "Sketch the [architecture, state machine, sequence]"
- "Map the [dependencies, components, boundaries]"
- Any explanation where the prose would lean heavily on words like "first… then… meanwhile… eventually" — those are sequence diagrams begging to be drawn

## When NOT to use this skill

This is the general fallback. When the prompt names a specific subject, hand off to the specialised skill that knows the conventions:

- **System architecture, microservices, deployment topology** → `html-architecture-diagrams` (service maps, ownership boundaries, on-call use)
- **Database schema, ERD, table relationships** → `html-erd-explorer` (PK/FK/cardinality, migrations)
- **Time axis, roadmap, Gantt, incident timeline** → `html-timeline-roadmap` (lanes, dependencies, "today" marker)

Use this skill when the diagram is conceptual or general-purpose (flowchart, state machine, sequence, dependency graph between abstract things). The specialised skills win when the subject is a real system, schema, or schedule.

## Output requirements

SVG inline using real `<svg>` and `<g>` elements. Use `viewBox` so the diagram scales without re-layout. Pair every diagram with a short prose explanation underneath — the diagram alone is rarely enough.

For multi-diagram pages, use one SVG per concept with its own caption rather than one giant SVG with everything.

## HTML output foundation

These defaults apply to **every** artifact this skill produces, on top of the requirements above. If a rule above conflicts with this list, the rule above wins; otherwise these are non-negotiable.

- **Output a real `.html` file the user opens in a browser — never inline-render in chat.** Every artifact this skill produces is a file on disk (`<topic>-<kind>.html`), not an HTML block embedded in the agent's chat surface (claude.ai artifact/canvas widgets, fenced ```html``` blocks, custom rendered iframes, etc.). Inline rendering strips features, themes unpredictably against the surrounding chat (often unreadable in dark mode), and lacks the stable origin and clipboard/network access the submit handler needs. Always write the file. The file itself must be self-contained: no build step, no external runtime, inline CSS and JS. Google Fonts via `<link>` is fine; otherwise nothing loaded from npm or a CDN unless this skill explicitly calls for it.
- **Mobile-responsive.** Collapse cleanly to a single column under ~700px so the artifact opens on a phone — including during incidents, commutes, and link-shares to non-laptop reviewers.
- **No `localStorage` / `sessionStorage` / `IndexedDB`.** Claude.ai artifacts can't use browser storage. State lives in JS memory; the export / copy button is the persistence layer.
- **Real semantic HTML, not screenshots.** Code goes in `<pre><code>` (selectable, copyable). Tabular data goes in `<table>`. Diagrams are inline `<svg>` with real `<g>` and `<path>` elements, not embedded PNGs. The reader should be able to copy any value, line, or label out of the artifact.
- **Build DOM safely; don't sling strings.** Use `textContent` for text and `document.createElement` + `appendChild` for structure. **Never** set `innerHTML` from a string that includes a variable, user input, computed value, or imported data — it's an XSS vector and many agent harnesses (including Claude Code) block it via security hooks. Static literal markup inline in your script is fine.
- **CSS variables for theme tokens.** Centralise colors, type, and spacing in `:root` so the whole artifact can be re-skinned in one place — and so design decisions are visible, not buried in 40 inline declarations.
- **Pick a deliberate aesthetic; skip the generic AI look.** No default purple gradient + Inter + three centered feature cards. Match the visual direction to the document's domain (utilitarian for ops, editorial for writeups, engineering for diagrams, etc.). Distinctive type pairings beat default sans on default sans.
- **Print- and PDF-readable.** `Cmd/Ctrl+P` should produce something usable: backgrounds that carry meaning print, content doesn't get clipped, dark themes have a sane print fallback.
- **Accessible by default.** Body text meets WCAG AA contrast. Interactive controls are keyboard-reachable and have visible focus states. Status and severity are conveyed by shape/label too, not color alone.
- **Visible last-updated timestamp** in the footer for any artifact someone might revisit (specs, diagrams, reports, roadmaps, dashboards). One-shot editors and ephemeral playgrounds can skip it.
- **Filename is part of the artifact.** Save with a descriptive name (`<topic>-<kind>.html`) so multiple artifacts on one project compose into a readable folder, not a pile of `output.html` collisions.

## Diagram types and when to pick them

### Flowchart / data-flow

For request/response paths, ETL pipelines, decision branches. Boxes for stages, arrows for direction of data, conditional diamonds for branches. Annotate edges with the data shape passing through.

### Sequence diagram

For interactions over time across multiple actors (services, components, processes). Vertical lifelines per actor, horizontal arrows for messages, time flowing downward. Number the steps.

### State machine

For things with discrete states and transitions (order status, connection status, UI mode). Circles for states, arrows for transitions, transitions labeled with the event that triggers them and the side effect.

### Architecture / component diagram

For "how the system fits together". Layers or zones, components inside, edges showing communication. Distinguish sync (solid) from async (dashed) edges. Show data ownership boundaries clearly.

### Dependency graph

For "what depends on what" — modules, packages, services. Nodes for things, directed edges for dependencies. Layer by depth or by group. Highlight cycles in red.

### Timeline / Gantt

For sequences with duration. Horizontal time axis, bars for activities, dependency arrows between bars. Mark milestones with vertical lines.

### Layered / sandwich

For stack-like concepts (network layers, abstraction layers, request lifecycle). Horizontal bands, each labeled, with concrete details inside.

## Text inside shapes — don't let it overflow

This is the most common failure mode for SVG diagrams: text bleeding past the edge of its box, crashing into adjacent labels, or rendering at a width the layout didn't account for. SVG `<text>` doesn't wrap automatically and the browser won't reflow your layout to make room. Two reliable patterns:

**Default: use `<foreignObject>` for any label longer than ~12 characters or that might vary.** Put real HTML inside — a `<div>` with CSS padding, `word-wrap: break-word`, and (optionally) `text-overflow: ellipsis`. Width and height of the `<foreignObject>` is fixed; the HTML inside wraps to fit. This is the only honest way to handle variable-length labels in SVG.

```html
<foreignObject x="100" y="60" width="180" height="60">
  <div xmlns="http://www.w3.org/1999/xhtml"
       style="width:100%;height:100%;padding:8px 12px;box-sizing:border-box;
              display:flex;align-items:center;justify-content:center;
              font:14px/1.3 system-ui;text-align:center;
              word-wrap:break-word;overflow-wrap:anywhere;">
    Order processing queue (high-priority)
  </div>
</foreignObject>
```

**For short, known-length labels only:** plain `<text>` is fine. Size the box around the label, not the other way around. Rough rule: box width ≥ `label.length × 8px + 32px padding` at 14px sans-serif. For multi-line labels with `<tspan>`, set `dy="1.2em"` per line and grow the box height accordingly.

**Concrete checklist before saving the file:**

1. **Did you measure?** No box should be set to a width you guessed. Either use `<foreignObject>` (HTML wraps) or compute width from label length.
2. **Padding ≥ 8px on every side** between text and the shape's edge. Cramped labels read as broken.
3. **Minimum 40px gap between adjacent nodes** so labels on one don't collide with labels on the neighbor when the diagram tightens.
4. **Long edge labels need a backing rect.** A label floating over a line in an arrow path becomes unreadable when the line crosses something else. Put a small white/background rect behind it.
5. **If a label is > 32 characters, you're probably wrong about it being a single line.** Either shorten it (the diagram is a sketch, not a paragraph) or wrap with `<foreignObject>`.
6. **Test mentally with the longest plausible value.** If the box is labeled "Service A" in the prompt but the real diagram has "Authentication & Authorization Service", the box needs to fit the real thing.

## Layout principles

- **Direction**: pick one (left-to-right or top-to-bottom) and stick with it across the whole diagram
- **Spacing**: leave generous whitespace between elements; cramped diagrams read as confused
- **Alignment**: align elements on a grid — diagonals are noise unless they convey something
- **Labels**: every box and every arrow gets a label; unlabeled arrows leave the reader guessing
- **Color**: use color to convey type or status, not decoration. Three colors max usually.
- **Type**: a single sans-serif at 1–2 sizes; resist the urge to vary

## Style direction

Avoid generic "boxes and arrows" defaults. Pick a deliberate style:

- **Editorial / sketch** — slightly hand-drawn feel, warm neutrals (Excalidraw-style)
- **Technical / engineering** — crisp lines, monospace labels, minimal color
- **Editorial / textbook** — confident type, serif labels, two-color emphasis
- **Modern / product-doc** — clean geometric, soft shadows, subtle color

The style should match the document the diagram lives in.

## Annotation patterns

- **Inline labels** — label sits on the arrow or inside the box
- **Margin annotations** — short notes pointing at specific elements with thin connecting lines
- **Step numbers** — for sequence diagrams, number arrows 1..N so prose can reference them
- **Legend** — when colors/shapes carry meaning, include a small legend

## Anti-patterns

- **Letting `<text>` overflow its box.** SVG text doesn't wrap; if you size a box for "Service A" and the label is "Authentication & Authorization Service", you get a broken-looking diagram with text bleeding into the next node. Use `<foreignObject>` with HTML inside for anything that isn't a short, known-length label, OR size the box from the label length, not the other way around. See the "Text inside shapes" section above.
- **Boxes touching adjacent labels.** Two nodes drawn close enough that one's label brushes the other's edge — the eye reads them as merged. Minimum 40px gap.
- **Edge labels floating directly over a path with nothing behind them.** When the path crosses something else, the label becomes unreadable. Put a small background-colored `<rect>` behind every edge label.
- Embedding a screenshot of a diagram drawn elsewhere. Use real SVG.
- Diagrams with no labels. The reader has to guess what each box is.
- More than ~12 elements in one diagram. Split into multiple zoom levels.
- Decorative arrows that don't convey direction. Every arrow should mean something.
- Recreating the same diagram in multiple visual styles in one document.

## Example prompt

> Read our rate-limiter code and produce a single HTML page with three diagrams: (1) the token-bucket data flow, (2) the request lifecycle as a sequence diagram, (3) the state machine for the bucket itself. Caption each. End with a "gotchas" section.

Output: HTML file with three labeled SVG diagrams in sequence (data flow → sequence → state machine), each captioned, followed by a gotchas section listing 3–5 non-obvious behaviors.
