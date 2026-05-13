---
name: html-architecture-diagrams
description: Create HTML system architecture diagrams — microservice maps, dependency graphs, deployment topologies, data ownership maps, integration diagrams. Useful during incidents, design reviews, onboarding, and capacity planning. Use whenever the user wants to visualize, document, or explain how a system fits together — across services, regions, queues, caches, databases, or organizational boundaries. Reach for this whenever the explanation would otherwise involve sentences like "service A talks to service B which writes to queue C".
---

# HTML Architecture & System Diagrams

Architecture diagrams answer the questions that come up most often during incidents and design reviews: what talks to what, who owns what, where does the data live, what fails when X goes down. A good HTML system diagram is the document you open during the incident, not the one you write after.

This skill is more focused than general SVG diagrams — specifically for system-level architecture.

## When to use this skill

- "Diagram our [system, architecture, services, infrastructure]"
- "Show me how X talks to Y"
- "Map our [microservices, dependencies, deployment, data flow]"
- "Document the architecture of Z for the design review"
- "Help an incident responder understand the system"

## Output requirements

Diagram as inline SVG. Include a legend if shapes/colors carry meaning. Save with a name like `<system>-architecture.html` and treat it as a versioned doc — these get opened during incidents, so the date in the footer matters.

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

## Diagram types

### Microservice map
Boxes for services. Edges for calls between them. Distinguish:
- **Sync calls** (solid arrows) from **async** (dashed arrows)
- **Internal** services from **third-party** (different fill or border)
- **Data ownership** by grouping services around the data store they own

For larger maps (~10+ services), group by domain into bounded zones.

### Deployment topology
Regions, VPCs, availability zones, k8s clusters, queues, caches, databases. Show physical/logical placement, not just service names. Include load balancers and ingress points. Mark single-region from multi-region resources.

### Dependency graph
Directed graph of "what depends on what". For monorepos: package-level. For services: service-level. Layer by depth. Highlight cycles in red — they're usually problems.

### Data flow
The path data takes through the system from ingress to storage. Each transformation/enrichment is a stage. Show queue boundaries clearly — they're often where incidents hide.

### Integration map
For systems that connect to many external services (CRM, payment, analytics, webhooks). The system in the middle, externals around it, edges labeled with what flows.

### Layered architecture
For showing abstraction layers (presentation / application / domain / infrastructure). Horizontal bands. Components inside. Cross-layer calls drawn explicitly.

## Conventions worth borrowing

### Edge styles
- **Solid** = synchronous request/response
- **Dashed** = asynchronous (queue, event)
- **Dotted** = optional / fallback path
- **Thick** = high-traffic / hot path
- **Red** = current incident / known problem area

### Shapes
- **Rectangle** = service or component
- **Cylinder** = data store (DB, blob storage, cache)
- **Hexagon or pill** = queue / topic
- **Cloud** = third-party / external
- **Person icon** = user / actor

### Color coding
Pick a meaning and stick to it across the diagram:
- By domain (auth=blue, billing=green, etc.)
- By criticality (red = tier-0, orange = tier-1, gray = tier-2)
- By owner (which team owns this)

Don't color for decoration. If color isn't conveying info, use neutral fills.

## Zoom levels

Big systems benefit from multi-zoom diagrams in one HTML file:

1. **System map** at the top — high-level zones, no internal detail
2. **Zone deep-dives** below — each zone expanded to show services
3. **Service deep-dives** further below — for the few services worth detailing

Link from the zone in the top map down to its detail section. The reader scrolls to the level they need.

## Annotations

System diagrams benefit from inline notes near specific elements:
- "Single point of failure"
- "Throughput: ~10k req/s"
- "Owned by Platform team"
- "Deprecated, migrating to X"

Use small margin notes connected by thin lines. Don't crowd the diagram itself.

## Anti-patterns

- "Box of arrows" diagrams with no legend. Reader has to guess what each style means.
- Showing only the happy path. Real systems have failure modes — show them.
- Out-of-date diagrams that look authoritative. Date-stamp visibly so readers can judge.
- Exhaustive detail at every zoom level. Pick one zoom per diagram.
- Hiding ownership. The person who owns a service is incident-relevant info.

## Example prompt

> Diagram our payments architecture as an HTML page. Three regions, payment service in each, a global ledger DB in us-east, async events to a fraud service, sync calls to two third-party processors. Show data ownership and mark the single point of failure.

Output: HTML file with an SVG topology showing three regional zones, services per region, the global ledger with explicit single-region marking, dashed lines to fraud service, solid lines to processors, color-coded by criticality, with a legend, last-updated timestamp, and a margin note flagging the global ledger as the SPOF.
