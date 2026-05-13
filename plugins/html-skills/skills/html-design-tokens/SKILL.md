---
name: html-design-tokens
description: Showcase design tokens — color palettes, type scales, spacing systems, radius scales, shadow systems, motion tokens — as HTML pages with copy-paste CSS variable exports, contrast ratio checks, and live sample type. Use whenever the user shows or asks about a palette, theme, design system, branding colors, design tokens, or wants to document any system of values that drives visual design. Markdown literally cannot display colors; reach for this skill any time color or spatial values are involved.
---

# HTML Design Token Showcases

Markdown can't show colors. Unicode block characters are a hack and a tell that the writer wished they had a different format. For palettes, type scales, spacing systems, and any other design tokens, use HTML — the values can be displayed for what they actually are.

## When to use this skill

- "Show me / document our [palette, colors, theme, tokens, design system]"
- "Build a token reference for X"
- "Document the spacing / type / color scale"
- Whenever a markdown file would have to fake a color with `█████` blocks
- Whenever a developer needs to copy CSS variables out of a doc

## Output requirements

Each token is shown:
1. Visually rendered (the actual color, the actual spacing, the actual shadow)
2. With its identifier (`--color-accent-500`, `space-md`)
3. With its value (`#B8602A`, `12px`)
4. With a copy button that puts the value or the CSS variable on the clipboard

Token grids reflow at narrow widths so the doc stays readable on a phone — designers and developers actually read these on the move.

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

## Sections to include

A complete token doc usually covers:

### Color
A grid of swatches. Each swatch shows: hex, the token name, contrast ratio against black and white (e.g., "AAA 7.2:1"). Group by hue family or by semantic role (primary/secondary/error/success).

### Type
Sample text rendered at every size in the scale. Show the font family, weight, size, line-height, and letter-spacing for each. Include a real sentence ("The quick brown fox…"), not lorem ipsum, so the reader can judge the type in context.

### Spacing
A row of progressively-larger blocks, each labeled with its token name and value. Optionally show common compositions (e.g., "card-padding = space-md (16px)").

### Radius
Squares at each radius value, labeled. Include the token name and the px value.

### Shadow / elevation
Cards at each elevation level on a neutral background, so the difference between levels is visible. Label with the token name and the box-shadow value.

### Motion (if applicable)
Animated samples for each duration/easing token. A button that replays the animation. Label with the token name and CSS value.

### Components (optional)
Small set of representative components rendered with the tokens applied. Helps the reader verify the tokens compose well.

## Copy interactions

For developers, the most useful interaction is "copy the CSS variable name" — they paste `var(--color-accent-500)` into their stylesheet. For designers, copying the raw value (`#B8602A`) is more useful.

Offer both. Click the swatch to copy the CSS variable, click the hex to copy the raw value. Show a brief "copied" indicator.

For bulk export, include a "Copy all as CSS variables" button at the bottom that produces:

```css
:root {
  --color-accent-500: #B8602A;
  --color-accent-400: #D88B5C;
  /* ... */
  --space-sm: 8px;
  --space-md: 16px;
  /* ... */
}
```

## Theme variants

If the system has light/dark/high-contrast variants, show them in a tab strip or side-by-side. Make the tab choice persist via URL hash so links can deep-link to a specific theme.

For light/dark, also show how the same component looks in each theme — colors don't tell the whole story.

## Contrast and accessibility

For colors that will be used as text or background, show the contrast ratio against the colors they'll pair with. Tag with WCAG levels (AA, AAA, fail). Don't sandbag — if a color fails AA on white, say so.

```
#B8602A on white: 4.7:1 — AA (large text only)
#B8602A on #2C2825: 4.2:1 — AA (large text only)
```

## Anti-patterns

- Hex codes without rendered swatches. Defeats the purpose of using HTML.
- Lorem ipsum in type samples. Use real-shaped sentences.
- Listing tokens without context. Group them; show how they compose.
- Skipping accessibility info. Designers ship inaccessible palettes when contrast isn't visible.
- Decorative animations that don't show the actual motion tokens. The motion section should let the reader see and feel the easing.

## Example prompt

> Document our brand palette as an HTML page. We have warm-neutral base colors (FAF8F5, F0EDE8, D4CFC7, 2C2825), a terracotta accent (B8602A), and muted text (8A837A). Show contrast ratios. Add a "copy as CSS variables" button.

Output: HTML page with a swatch grid for each color showing rendered swatch + name + hex + contrast ratios against black/white, with click-to-copy and a bulk export button at the bottom.
