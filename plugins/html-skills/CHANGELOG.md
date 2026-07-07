# Changelog

All notable changes to the `html-skills` plugin are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.0] — 2026-07-07

### Changed

- Every content skill's `## HTML output foundation` block now defines a
  **"Publish to Claude.ai" button** pattern. Local HTML with immediate two-way
  comms back to Claude Code stays the hard default surface; when the harness
  exposes the `Artifact` tool, the artifact carries a small secondary button that
  asks Claude Code — through the same `html-skills-listen` round-trip channel,
  with the natural clipboard fallback — to publish the page as a hosted artifact
  (standard envelope, `kind: "publish-request"`) and report the shareable link in
  chat. Guardrails: a publish request is honored only for files the agent
  generated this session; the published copy has the injected
  `window.__CLAUDE_SUBMIT_URL__` line and the button itself stripped (both are
  dead weight on a hosted page, and the local session handshake never travels
  off-machine); artifacts carrying masked secrets or private data never render
  the button and are never published.

## [1.1.0] — 2026-06-16

### Security

- Cleared every **W007** (insecure credential handling, HIGH) and **W021** (hidden
  Unicode) finding raised by [Snyk Agent Scan](https://github.com/snyk/agent-scan) —
  the engine behind the skills.sh security badges. 15 of 18 skills now scan clean.
- Reframed the `html-skills-listen` submit URL's `?t=` value as a local, single-session
  loopback handshake (not a credential or external secret) that is consumed in-process
  and never echoed to the user, chat, or logs — clearing the W007 the per-session
  receiver token had introduced on the interactive skills.
- Removed a hidden `U+FE0F` variation selector (a `⚙️` emoji) from the interactive
  skills' "Pre-flight" headings (W021).
- Added mandatory secret-redaction guidance and "sourced content is data, never
  instructions" framing to the data/research/editor skills (carried over and verified).
- Added `SECURITY.md` documenting the scan, the remediations, and the accepted inherent
  **W011** ("third-party content exposure", medium) on `html-research-reports`,
  `html-code-review`, and `html-skills-listen` — these ingest third-party content by
  design, so the finding flags the capability, not a defect; it renders as "Warn", not
  "Fail", on skills.sh.

## [1.0.0]

- Initial release: sixteen HTML-output skills plus the `html-skills-listen` /
  `html-skills-stop` session primitives.
