---
name: html-slideshow-deck
description: Generate keyboard-navigable HTML slideshow decks for presentations, tech talks, leadership briefings, onboarding walkthroughs, and any sequential visual narrative. Use whenever the user wants slides, a deck, a presentation, a tech talk, a brown-bag, a briefing, or any sequential walkthrough — especially when they want to share via a link rather than as a PowerPoint or Keynote file. Prefer HTML over .pptx whenever the deck contains live code, embedded interactivity, or will be shared as a URL.
---

# HTML Slideshow Decks

For presentations that need to be shared as a link, contain real code or live interactivity, or be quickly assembled from existing source material, an HTML deck beats PowerPoint. It opens in any browser, presents fullscreen, and embeds anything HTML embeds.

## When to use this skill

- "Make me slides / a deck / a presentation for X"
- "Tech talk on X"
- "Brief leadership on Y"
- "Walking deck for new hires on Z"
- "Lightning talk / brown-bag on W"
- Whenever the deliverable is sequential and visual but the user wants a URL, not a file

For decks intended for corporate distribution (board meetings, customer pitches), still consider .pptx. For internal tech talks and async sharing, prefer HTML.

## Output requirements

Keyboard-navigable: `→`/`space` for next, `←` for previous, `f` for fullscreen, `Esc` to exit fullscreen. Fixed 16:9 slide aspect ratio (or 16:10), centered with letterboxing on wider/narrower screens.

Each slide is a `<section>` with class `slide`. The active slide is shown; others hidden. URL hash (`#3`) updates with slide number so direct linking works.

Include a thin progress bar or slide counter (e.g., "4 / 17") in a corner.

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

1. **Title slide** — title, subtitle, presenter, date
2. **Hook / motivation** — why anyone should care
3. **Body slides** — the substance
4. **Recap** — the three things the audience should remember
5. **Q&A / closing** — call to action, contact info

Don't pad. A 15-minute talk is ~12–15 slides for tech, fewer for narrative. More than 30 slides for a short talk usually means the speaker is reading, not presenting.

## Slide types

### Title slide
Big serif or display font for the title. Subtitle smaller. Presenter name + date. No bullet points.

### One-idea slide
The default. One headline at the top, one visual or short prose body. The audience should be able to read everything in 5 seconds and then look at the speaker.

### Code slide
Monospace, generously sized. Highlight the line(s) being discussed. Don't put more than ~10 lines of code on a slide; if more is needed, split across slides with the cursor moving down.

### Diagram slide
Inline SVG diagram, big enough to read from the back of a room. Caption underneath, not crowded.

### Comparison slide
Two or three columns side-by-side. Use it sparingly; comparison slides eat reading time.

### Demo slide
Live HTML embedded right in the slide — a working button, a live chart, a small playground. The HTML deck's superpower.

### Section break
Just a phrase on a colored background. Resets attention before a new theme.

### Recap slide
Three bullets. The actual takeaways. Keep it short — the audience writes these down.

## Style direction

Pick a deliberate aesthetic and apply it consistently across slides. Defaults to avoid: bullet-heavy white-on-white, clip art, anything that smells like a corporate template.

Strong directions:
- **Editorial** — large serif headlines, generous whitespace, sparse color
- **Engineering** — monospace dominance, dark theme, single accent color
- **Brutalist** — heavy type, asymmetric layouts, bold flat color blocks
- **Documentary** — full-bleed photography (or geometric stand-ins), white type overlay

Pick one and commit. Mixed styles read as inconsistent.

## Speaker notes

For decks that will be presented live, support a presenter mode: pressing `n` toggles speaker notes (a sidebar showing notes for the current slide). Notes are written into `<aside>` inside each `<section>`.

## Building from source material

A common use is "build a deck from this codebase / this article / these notes". When doing this:

- Don't quote source text verbatim. Distill into one-idea-per-slide phrasing.
- Pull out the 3–5 strongest examples; don't try to cover everything.
- Generate diagrams to replace prose where possible.
- End with the "so what" — what the audience should do or remember.

## Anti-patterns

- Walls of bullets. If a slide needs more than 3 short bullets, it needs to be split or rewritten.
- Reading the slides aloud. Slides should support the speaker, not duplicate them.
- Text smaller than ~24pt body. Audiences squinting are audiences disengaging.
- Animations that don't carry meaning. A slide flying in just delays the content.
- Color schemes with insufficient contrast — projectors wash out everything.

## Example prompt

> Build me an HTML deck for an internal lightning talk on the new evaluation framework. 12 slides max, code-heavy in the middle, end with three takeaways. Use a monospace-dominant engineering aesthetic. Include speaker notes I can toggle.

Output: HTML deck with title slide, motivation, 8–9 body slides (mix of one-idea + code + one diagram), recap, and closing. Presenter mode with notes per slide. Keyboard navigation. Progress indicator in the corner.
