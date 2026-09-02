# agent-html-skills — conventions for Claude Code

## Versioning (required)

**Always bump the plugin version on every update — never ship changed code under the
same version string.**

- The version lives in `plugins/html-skills/.claude-plugin/plugin.json` → `"version"`.
- Every skill's `SKILL.md` frontmatter carries the same version in `metadata.version`
  (ecosystem sites read individual skills, so per-skill versions must match the plugin
  version). Don't edit the 19 files by hand — run
  `python3 scripts/sync-skills.py --set X.Y.Z` to bump plugin.json and stamp every skill
  in one step (or `--write` to re-sync after a manual plugin.json bump). The script has no
  third-party dependencies.
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

## Shared skill sections (single-sourced)

Every content skill repeats the same `## Pre-flight`, `## HTML output foundation`, and
(interactive skills only) `## Submit pipeline` sections verbatim, because skills load
independently and skills.sh reads one `SKILL.md` at a time. Don't edit those copies:

- The templates live in `plugins/html-skills/assets/blocks/{preflight,foundation,submit}.md`.
- Each copy sits between `<!-- block:NAME -->` … `<!-- /block:NAME -->` markers.
- Edit the template, then run `python3 scripts/sync-skills.py --write` to push it into
  every skill. `--check` (run by CI) fails on any drift, on an unbraced
  `$CLAUDE_PLUGIN_ROOT`, on a `name` that doesn't match the skill directory, on a
  `description` over 1,024 characters (skills.sh limit), or on `description` +
  `when_to_use` over 1,536 characters (Claude Code truncates the pair in the skill listing).

## Skill descriptions

`description` is what every agent reads (skills.sh, `npx skills`, Cursor, Codex…), so it
keeps the strongest trigger phrases. `when_to_use` is Claude-Code-only extra trigger text
read alongside the description; keep the pair under the 1,536-character listing limit.
Descriptions are deliberately pushy — don't soften them. Changing wording in the
data/research/editor skills can re-trigger the skills.sh Snyk scan (W007 is
wording-sensitive); see `plugins/html-skills/SECURITY.md` and re-scan before tagging.

## CI

`.github/workflows/version-check.yml` runs on every PR to `main`: a version-bump +
changelog check, `scripts/sync-skills.py --check`, and `claude plugin validate --strict`
on the marketplace manifest, the plugin, and the skills directory.
