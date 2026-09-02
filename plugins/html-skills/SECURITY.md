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

**17 of 19 skills scan clean** on the 1.3.0 release (September 2026 scan). The remaining 2 —
`html-research-reports` and `html-testing-checklist` — carry one accepted, inherent `W011`
"third-party content exposure" finding each (see below). No `W007` (high) findings: the
1.3.0 rewording (shorter descriptions, `when_to_use`, condensed shared blocks, the
browser-storage rule) did not re-trigger the credential-handling judge.

For comparison, the June 2026 scan of 1.1.0 was 15 of 18 clean, with `W011` also on
`html-code-review` and `html-skills-listen`; both are clear in the September scan.

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

## Accepted (inherent) — W011 "Third-party content exposure" (medium)

| Skill | Why the finding is inherent |
|---|---|
| `html-research-reports` | synthesizes Slack / Linear / web / git-history (outsider-authored) into reports — that is the skill's purpose |
| `html-testing-checklist` | pulls tracker items (Monday, Linear, Jira, GitHub) and reads each ticket's body and comment thread to ground the test steps — that is the skill's purpose |

These skills ingest third-party content **by design**. `W011` flags the *capability*,
not a defect, and it cannot be cleared without removing what the skill does. The residual
risk is mitigated in the skill instructions: sourced/submitted content is treated strictly
as data (never as instructions), quoted text is rendered inert via `textContent`, every
source-derived value is HTML-escaped, embedded snippets pass a mandatory credential
redaction, and the agent is explicitly barred from acting on directives embedded in that
content or letting retrieved content expand the task's scope.

On skills.sh this surfaces as **"Warn," not "Fail."** Rewording these findings was tested
and found counterproductive — re-touching the data-flow wording re-triggers the `W007`
"verbatim value" judge — so they are accepted as-is.

## In CI

`.github/workflows/snyk-agent-scan.yml` runs the scan on every PR that touches the skills,
on pushes to `main`, weekly, and on demand (`SNYK_TOKEN` repository secret). The raw JSON is
uploaded as a workflow artifact, and `scripts/snyk-gate.py` fails the job on any finding
not in its `ACCEPTED` list — which mirrors the table above; change the two together. A
scan that stops reporting an accepted finding produces a warning, not a failure, so this
file can be updated.

Locally, the same gate runs as:

```bash
SNYK_TOKEN=<your-token> uvx snyk-agent-scan@latest \
  --skills plugins/html-skills/skills --json > snyk-scan.json
python3 scripts/snyk-gate.py snyk-scan.json
```
