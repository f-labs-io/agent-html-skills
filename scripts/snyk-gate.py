#!/usr/bin/env python3
"""Gate CI on Snyk Agent Scan output.

Reads the `--json` output of `snyk-agent-scan --skills plugins/html-skills/skills` and fails
unless every finding is on the accepted list below. That list mirrors the "Accepted
(inherent)" section of plugins/html-skills/SECURITY.md — update both together.

Usage:
  scripts/snyk-gate.py snyk-scan.json

Exit 0: no findings, or only accepted ones.
Exit 1: a finding that isn't accepted, a server-level risk, fewer skills scanned than the
        repo contains, or output the script can't read.

Accepted findings that no longer fire are reported as a warning so SECURITY.md can be
updated, but they don't fail the build.
"""

import glob
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_GLOB = str(REPO_ROOT / "plugins/html-skills/skills/*/SKILL.md")

# skill name -> risk-index keys accepted as inherent to what the skill does.
# "third_party_content_exposure" is Snyk's W011 (third-party content / indirect prompt injection).
ACCEPTED = {
    "html-research-reports": {"third_party_content_exposure"},
    "html-testing-checklist": {"third_party_content_exposure"},
}


def in_ci():
    return os.environ.get("GITHUB_ACTIONS") == "true"


def emit(kind, msg):
    print(f"::{kind}::{msg}" if in_ci() else f"{kind.upper()}: {msg}")


def main(path):
    try:
        doc = json.loads(Path(path).read_text())
    except Exception as exc:
        emit("error", f"could not read scan output {path}: {exc}")
        return 1

    responses = doc.get("scan_path_responses") if isinstance(doc, dict) else None
    if not isinstance(responses, list):
        emit("error", "unrecognized scan output (no scan_path_responses) — inspect the uploaded artifact")
        return 1

    rows = []          # (skill, risk, score, status)
    violations = []
    seen = set()
    for resp in responses:
        if resp.get("server_risks"):
            violations.append(f"server-level risks reported: {json.dumps(resp['server_risks'])[:300]}")
        for skill in resp.get("skill_risks") or []:
            name = skill.get("name", "?")
            seen.add(name)
            risks = skill.get("risk_indexes") or {}
            if not risks:
                rows.append((name, "-", "", "clean"))
                continue
            for key, detail in risks.items():
                detail = detail if isinstance(detail, dict) else {}
                score = detail.get("score", "")
                accepted = key in ACCEPTED.get(name, set())
                rows.append((name, key, score, "accepted" if accepted else "NEW"))
                if not accepted:
                    evidence = (detail.get("evidence") or "")[:240]
                    violations.append(f"{name}: {key} (score {score}) — {evidence}")

    expected = {Path(p).parent.name for p in glob.glob(SKILLS_GLOB)}
    missing = sorted(expected - seen)
    if missing:
        violations.append(f"scanner returned no result for: {', '.join(missing)}")

    cleared = [
        f"{name}: {key}"
        for name, keys in ACCEPTED.items()
        for key in keys
        if not any(r[0] == name and r[1] == key for r in rows)
    ]

    # Summary table: stdout, and the job summary when running in Actions.
    width = max(len(r[0]) for r in rows) if rows else 20
    lines = [f"{'skill':{width}}  {'finding':34} {'score':>5}  status"]
    for name, key, score, status in sorted(rows):
        lines.append(f"{name:{width}}  {key:34} {str(score):>5}  {status}")
    table = "\n".join(lines)
    print(table)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write("## Snyk Agent Scan\n\n```\n" + table + "\n```\n")
            if cleared:
                fh.write("\nAccepted findings that no longer fire: " + ", ".join(cleared) + "\n")

    clean = sum(1 for r in rows if r[3] == "clean")
    print(f"\n{clean} of {len(seen)} skills clean; {sum(1 for r in rows if r[3] == 'accepted')} accepted finding(s)")

    for item in cleared:
        emit("warning", f"accepted finding no longer reported — consider updating SECURITY.md and ACCEPTED: {item}")
    if violations:
        for v in violations:
            emit("error", v)
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
