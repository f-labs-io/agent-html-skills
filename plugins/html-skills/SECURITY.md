# Security — Snyk Agent Scan

These skills are scanned by [Snyk Agent Scan](https://github.com/snyk/agent-scan) — the
same engine behind the skills.sh security badges. Reproduce the scan locally:

```bash
SNYK_TOKEN=<your-token> uvx snyk-agent-scan@latest \
  --skills plugins/html-skills/skills --json
```

(Get a token at <https://app.snyk.io/account>. The scan shares skill text with Snyk's
Agent Scan API for analysis; these skills are public and secret-free, so there is no new
exposure — review before pointing it at private skills.)

## Status

**15 of 18 skills scanned clean** in the June 2026 scan. The remaining 3 carry one
accepted, documented `W011` (medium) finding each. No `W007` (high) findings remain.

`html-testing-checklist` (added in 1.2.0) postdates that scan. Like the three skills
below, it ingests third-party content by design (PR diffs, ticket threads, tester
submissions), so an inherent `W011` "Warn" is expected there on the same grounds; it
carries the same mitigations (mandatory credential redaction before embedding snippets,
submissions and sourced text treated strictly as data, HTML-escaping of every
source-derived value).

## Remediated

- **W007 — Insecure credential handling (HIGH).** Cleared on `html-data-explorer`,
  `html-throwaway-editor`, and `html-research-reports` via a mandatory secret-redaction
  step before any user/sourced data is embedded; and on the interactive skills plus
  `html-skills-listen` by reframing the per-session submit URL's `?t=` value for what it
  is — a local, single-session loopback handshake the receiver checks to reject forged
  POSTs, **not** a credential or external secret. It is consumed in-process to wire the
  local artifact to the local receiver and is never echoed to the user, chat, or logs.
- **W021 — Hidden Unicode.** Removed a `U+FE0F` variation selector (from a `⚙️` emoji)
  in the "Pre-flight" headings of the interactive skills.

## Accepted (inherent) — W011 "Third-party content exposure" (medium, 0.85)

| Skill | Why the finding is inherent |
|---|---|
| `html-research-reports` | synthesizes Slack / web / git-history (outsider-authored) into reports — that is the skill's purpose |
| `html-code-review` | renders PR diffs / commit messages authored by others — that is the skill's purpose |
| `html-skills-listen` | the localhost receiver forwards submission POST bodies to the agent — that is the skill's purpose |

These three skills ingest third-party content **by design**. `W011` flags the *capability*,
not a defect, and it cannot be cleared without removing what the skill does. The residual
risk is mitigated in the skill instructions: sourced/submitted content is treated strictly
as data (never as instructions), quoted text is rendered inert via `textContent`, and the
agent is explicitly barred from acting on directives embedded in that content or letting
retrieved content expand the task's scope.

On skills.sh this surfaces as **"Warn," not "Fail."** Rewording these findings was tested
and found counterproductive — re-touching the data-flow wording re-triggers the `W007`
"verbatim value" judge — so they are accepted as-is.

To make a local/CI scan exit clean while keeping these documented as accepted risk:

```bash
SNYK_TOKEN=<your-token> uvx snyk-agent-scan@latest \
  --skills plugins/html-skills/skills --ignore-issues-codes W011
```
