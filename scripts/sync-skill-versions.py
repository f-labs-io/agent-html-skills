#!/usr/bin/env python3
"""Keep every skill's frontmatter `metadata.version` in sync with the plugin release version.

The plugin release version in plugins/html-skills/.claude-plugin/plugin.json is the
single source of truth (it is what drives Claude Code marketplace update delivery).
Each SKILL.md additionally carries the same version in its frontmatter `metadata.version`
so ecosystem sites that read individual skills (skills.sh, standalone .skill repackaging)
see the release a skill shipped in. This script keeps the two from drifting.

Usage:
  scripts/sync-skill-versions.py --check          # validate (CI mode); exit 1 on any drift
  scripts/sync-skill-versions.py --write          # stamp/update every SKILL.md to the plugin version
  scripts/sync-skill-versions.py --set 1.3.0      # bump plugin.json AND stamp every SKILL.md

Checks enforced by --check:
  - plugin.json parses and its version is strict semver (X.Y.Z)
  - every skills/*/SKILL.md has YAML frontmatter that parses, with name + description
  - every frontmatter has metadata.version, as a string, equal to the plugin version
  - every description is under 1024 characters (skills.sh / Agent Skills limit)

Requires PyYAML (pip install pyyaml).
"""

import argparse
import glob
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_JSON = REPO_ROOT / "plugins/html-skills/.claude-plugin/plugin.json"
SKILLS_GLOB = str(REPO_ROOT / "plugins/html-skills/skills/*/SKILL.md")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
DESCRIPTION_LIMIT = 1024

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")


def rel(path):
    return str(Path(path).resolve().relative_to(REPO_ROOT))


def plugin_version():
    manifest = json.loads(PLUGIN_JSON.read_text())
    version = manifest.get("version", "")
    if not SEMVER.match(version):
        sys.exit(f"{rel(PLUGIN_JSON)}: version {version!r} is not strict semver (X.Y.Z)")
    return version


def skill_files():
    files = sorted(glob.glob(SKILLS_GLOB))
    if not files:
        sys.exit(f"no SKILL.md files matched {SKILLS_GLOB}")
    return files


def split_frontmatter(path):
    text = Path(path).read_text()
    match = FRONTMATTER.match(text)
    if not match:
        return text, None, None
    return text, match.group(1), match


def check(version):
    errors = []
    for path in skill_files():
        name = rel(path)
        _, fm_text, _ = split_frontmatter(path)
        if fm_text is None:
            errors.append(f"{name}: no YAML frontmatter block")
            continue
        try:
            fm = yaml.safe_load(fm_text)
        except yaml.YAMLError as exc:
            errors.append(f"{name}: frontmatter is not valid YAML ({exc})")
            continue
        if not isinstance(fm, dict) or not fm.get("name") or not fm.get("description"):
            errors.append(f"{name}: frontmatter must define name and description")
            continue
        if len(fm["description"]) >= DESCRIPTION_LIMIT:
            errors.append(
                f"{name}: description is {len(fm['description'])} chars "
                f"(limit {DESCRIPTION_LIMIT})"
            )
        skill_version = (fm.get("metadata") or {}).get("version")
        if skill_version is None:
            errors.append(f"{name}: missing metadata.version (expected \"{version}\")")
        elif not isinstance(skill_version, str):
            errors.append(f"{name}: metadata.version must be a quoted string")
        elif skill_version != version:
            errors.append(
                f"{name}: metadata.version \"{skill_version}\" != plugin version "
                f"\"{version}\" — run scripts/sync-skill-versions.py --write"
            )
    if errors:
        for err in errors:
            print(f"::error::{err}" if in_ci() else f"ERROR: {err}")
        return 1
    print(f"OK: {len(skill_files())} skills all carry metadata.version \"{version}\"")
    return 0


def in_ci():
    import os

    return os.environ.get("GITHUB_ACTIONS") == "true"


def write(version):
    stamp = f'metadata:\n  version: "{version}"\n'
    changed = []
    for path in skill_files():
        text, fm_text, match = split_frontmatter(path)
        if fm_text is None:
            sys.exit(f"{rel(path)}: no YAML frontmatter block — fix by hand first")
        if re.search(r"^metadata:", fm_text, re.M):
            if re.search(r"^  version: ", fm_text, re.M):
                # metadata.version is the only `  version:` key in these frontmatters
                new_fm = re.sub(r"^  version: .*$", f'  version: "{version}"', fm_text, count=1, flags=re.M)
            else:
                new_fm = re.sub(r"^metadata:$", f'metadata:\n  version: "{version}"', fm_text, count=1, flags=re.M)
        else:
            new_fm = fm_text + "\n" + stamp.rstrip("\n")
        if new_fm != fm_text:
            Path(path).write_text(f"---\n{new_fm}\n---\n" + text[match.end():])
            changed.append(rel(path))
    # verify what we wrote
    if check(version) != 0:
        sys.exit("post-write verification failed — inspect the files above")
    if changed:
        print(f"stamped {len(changed)} file(s):")
        for name in changed:
            print(f"  - {name}")
    else:
        print("already in sync — nothing to write")


def set_plugin_version(new_version):
    if not SEMVER.match(new_version):
        sys.exit(f"--set {new_version!r} is not strict semver (X.Y.Z)")
    text = PLUGIN_JSON.read_text()
    new_text, count = re.subn(r'"version": "\d+\.\d+\.\d+"', f'"version": "{new_version}"', text, count=1)
    if count != 1:
        sys.exit(f"{rel(PLUGIN_JSON)}: could not find a single version field to replace")
    PLUGIN_JSON.write_text(new_text)
    json.loads(new_text)
    print(f"{rel(PLUGIN_JSON)} -> {new_version}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="validate; exit 1 on drift (CI mode)")
    mode.add_argument("--write", action="store_true", help="stamp every SKILL.md to the plugin version")
    mode.add_argument("--set", metavar="X.Y.Z", help="bump plugin.json, then stamp every SKILL.md")
    args = parser.parse_args()

    if args.set:
        set_plugin_version(args.set)
        write(args.set)
        print("remember: update plugins/html-skills/CHANGELOG.md and tag vX.Y.Z after merge")
        return 0
    version = plugin_version()
    if args.check:
        return check(version)
    write(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
