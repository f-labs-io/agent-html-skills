---
name: html-timeline-roadmap
description: Create HTML timelines and roadmaps with status pills, dependency arrows, and milestone markers — for quarterly planning, project retrospectives, release histories, incident timelines, sprint visualizations. Use whenever the user wants to visualize a sequence of events over time, a plan, a roadmap, a release schedule, or look back at how a project unfolded. Reach for this whenever the explanation has a clear time axis, even if the user doesn't say "timeline".
---

# HTML Timeline & Roadmap Views

Timelines are how humans think about anything with a time axis. Roadmaps, retrospectives, release histories, incident timelines, sprint plans — they all benefit from seeing time horizontally.

## When to use this skill

- "Make me a roadmap / timeline / Gantt for X"
- "Plan the next [quarter, 6 months, year]"
- "Visualize the release history / sprint plan / project schedule"
- "Build a retrospective timeline showing how X unfolded"
- "Map the incident timeline"
- Any explanation where time order matters and the time spans are visible

## Output requirements

Time runs horizontally (left=past, right=future). On a phone, time runs vertically with bars rendered as stacked cards — that's the responsive collapse for this skill.

Include:
- A clear time axis with appropriate granularity (days for incidents, weeks for sprints, months for roadmaps, quarters for annual plans)
- "Today" marker if the timeline straddles now

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

1. **Header** — title, time range covered, last updated
2. **Time axis** — at the top, with major and minor gridlines
3. **Lanes** — horizontal rows, one per workstream / team / category
4. **Items** — bars/pills positioned by time, sized by duration
5. **Dependencies** — arrows between items (when the next can't start until the prior finishes)
6. **Milestones** — vertical markers at specific dates
7. **Legend** — for status colors and shape conventions
8. **Detail panel** — click an item to see its full info

## Patterns

### Pattern A: Roadmap (forward-looking)

Lanes per team/area. Bars per initiative, sized by estimated duration. Status pills (Planned / In Progress / At Risk / Shipped). Dependency arrows between bars where ordering matters. "Today" line.

Granularity: months or quarters. Don't pretend more precision than you have.

### Pattern B: Sprint / iteration plan

Smaller granularity (days/weeks). Lanes per IC or per workstream. More detail per item. Status updated daily. Often shows velocity metrics in a summary panel.

### Pattern C: Release history (backward-looking)

Past releases on the timeline. Each release is a milestone with its version label. Annotations for major events (incidents, hires, decisions). Useful for retrospectives and onboarding new hires to project context.

### Pattern D: Project retrospective timeline

A specific project's journey. Decision points marked. Things that went well in green, things that went poorly in red. Free-text annotations. Optional "alternate path" branch showing what could have happened.

### Pattern E: Incident timeline

Minute-level granularity. Stack of events with annotations: detection, escalation, mitigation, resolution. Color-coded by severity/owner. Often has a synthetic "user-impact" lane showing customer-facing effect over time.

### Pattern F: Gantt-style with critical path

For project planning with hard dependencies. Critical path highlighted. Slack visible (light bars showing buffer). Dependency arrows everywhere.

## Status conventions

Use a small fixed vocabulary:

- 🟢 **On track** / **Shipped** — solid green
- 🟡 **At risk** / **Slipping** — solid amber
- 🔴 **Blocked** / **Failed** — solid red
- ⚪ **Not started** / **Planned** — outlined
- ➖ **Cancelled** — strikethrough or muted

Show the legend, even if you think it's obvious.

## Dependency arrows

Use arrows sparingly. Every arrow draws attention; an arrow on every transition makes the diagram unreadable. Show arrows for:
- Hard dependencies (B can't start until A finishes)
- Cross-team handoffs
- The critical path

Don't show arrows for things that just happen to be near each other.

## Density

For long roadmaps or many lanes, density matters:

- **High density**: 6+ lanes, items closely packed. Use small text, group items, allow expand-on-click.
- **Medium density**: 3–5 lanes, breathing room around items. Default for most cases.
- **Low density**: 1–2 lanes, large items, generous spacing. For hero timelines (single project arc).

Match density to the audience. Leadership briefings should be lower density than internal sprint plans.

## Annotations

Free-text annotations attached to specific dates ("$X funded — Mar 14", "Incident A — Jun 2") are what make timelines tell stories rather than just show schedules. Use them generously but anchor each to a specific date.

## Anti-patterns

- Roadmaps with quarter-granularity but day-precise dates. Pick a granularity and stop pretending.
- All bars green. If everything's on track, the status pills are decoration.
- Arrows from every item to every adjacent item. Reserve arrows for actual dependencies.
- Forgetting "today". Without it, a roadmap is just a list of dates.
- Stale roadmaps that look authoritative. Date-stamp prominently and update.

## Example prompt

> Build me an HTML roadmap for the next two quarters. Three lanes (Platform, AI, Infra), eight initiatives total, status pills, dependency arrows where Platform work blocks AI work. Mark today.

Output: HTML file with a time axis showing 6 months in monthly columns, three lanes, eight bars positioned and sized accordingly, status pills, two dependency arrows from Platform items to AI items, a "today" vertical line, click-to-expand details.
