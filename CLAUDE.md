# agent-html-skills — conventions for Claude Code

## Versioning (required)

**Always bump the plugin version on every update — never ship changed code under the
same version string.**

- The version lives in `plugins/html-skills/.claude-plugin/plugin.json` → `"version"`.
- Every skill's `SKILL.md` frontmatter carries the same version in `metadata.version`
  (ecosystem sites read individual skills, so per-skill versions must match the plugin
  version). Don't edit the 19 files by hand — run
  `python3 scripts/sync-skill-versions.py --set X.Y.Z` to bump plugin.json and stamp
  every skill in one step (or `--write` to re-sync after a manual plugin.json bump).
  CI (`skill-versions` job in `.github/workflows/version-check.yml`) fails the PR on
  any drift; `--check` runs the same validation locally.
- Bump the **minor** (`x.Y.0`) for new skills or any behaviour/instruction change; bump the
  **patch** (`x.y.Z`) for small fixes (typos, tiny tweaks). Never reuse a released version.
- Update `plugins/html-skills/CHANGELOG.md` in the same change.
- After the release merges to `main`, tag it: `git tag vX.Y.Z && git push origin vX.Y.Z`
  (matches the existing `v1.0.0` tag convention).
- This bump is also load-bearing for **skills.sh**: it re-audits a skill only when the
  version string changes, so bumping is what refreshes the security badges.
- Do **not** confuse this with the submit-payload `version: 1` inside the interactive
  skills' `SKILL.md` / `submit-handler.js` — that is the JSON envelope schema version and
  is unrelated to the plugin release version.
