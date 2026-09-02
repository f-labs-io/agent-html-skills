#!/usr/bin/env python3
"""Keep the html-skills SKILL.md files in sync with the plugin release.

Two things are repeated across the 19 skills and must never drift:

  1. `metadata.version` in every SKILL.md frontmatter equals the plugin version in
     plugins/html-skills/.claude-plugin/plugin.json (the single source of truth that
     drives marketplace update delivery).
  2. The shared blocks (pre-flight, HTML output foundation, submit pipeline) are
     repeated verbatim in each skill so every SKILL.md stays self-contained for
     skills.sh and standalone repackaging. Their single source of truth is
     plugins/html-skills/assets/blocks/<name>.md; each copy sits between
     `<!-- block:<name> -->` and `<!-- /block:<name> -->` markers.

Usage:
  scripts/sync-skills.py --check          # validate (CI mode); exit 1 on any drift
  scripts/sync-skills.py --write          # stamp versions and re-sync every block
  scripts/sync-skills.py --set 1.4.0      # bump plugin.json, then --write

Checks enforced by --check:
  - plugin.json parses and its version is strict semver (X.Y.Z)
  - every skills/*/SKILL.md has frontmatter with name, description, license, metadata.version
  - name equals the skill's directory name (what the plugin namespaces on)
  - description <= 1024 chars (skills.sh / Agent Skills limit)
  - description + when_to_use <= 1536 chars (Claude Code truncates the pair in the listing)
  - metadata.version is a quoted string equal to the plugin version
  - every content skill carries the preflight and foundation blocks; interactive skills
    also carry the submit block; each block matches its template exactly
  - no unbraced `$CLAUDE_PLUGIN_ROOT` (Claude Code only substitutes `${CLAUDE_PLUGIN_ROOT}`)

No third-party dependencies: a small parser handles the YAML subset these frontmatters
use (plain and quoted scalars, `>-` / `>` / `|` / `|-` block scalars, one level of nested map).
"""

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins/html-skills"
PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin/plugin.json"
SKILLS_GLOB = str(PLUGIN_DIR / "skills/*/SKILL.md")
BLOCKS_DIR = PLUGIN_DIR / "assets/blocks"

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
BLOCK = re.compile(r"<!-- block:([a-z-]+) -->\n(.*?)\n<!-- /block:\1 -->", re.S)
DESCRIPTION_LIMIT = 1024
LISTING_LIMIT = 1536

# Session primitives carry no shared blocks; every other skill is a content skill.
PRIMITIVES = {"html-skills-listen", "html-skills-stop"}
REQUIRED_BLOCKS = ("preflight", "foundation")
INTERACTIVE_BLOCK = "submit"


# ---------------------------------------------------------------- frontmatter

def _unquote(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    return raw


def parse_frontmatter(text):
    """Parse the YAML subset used by these SKILL.md files into a dict."""
    lines = text.split("\n")
    data, i, n = {}, 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):(.*)$", line)
        if not m:
            raise ValueError(f"line {i + 1}: expected 'key: value', got {line!r}")
        key, rest = m.group(1), m.group(2).strip()
        if rest in (">", ">-", "|", "|-"):
            block = []
            i += 1
            while i < n and (lines[i].startswith("  ") or not lines[i].strip()):
                block.append(lines[i][2:] if lines[i].startswith("  ") else "")
                i += 1
            while block and not block[-1].strip():
                block.pop()
            if rest.startswith(">"):
                paragraphs, current = [], []
                for ln in block:
                    if ln.strip():
                        current.append(ln.strip())
                    else:
                        paragraphs.append(" ".join(current))
                        current = []
                paragraphs.append(" ".join(current))
                value = "\n".join(paragraphs)
            else:
                value = "\n".join(block)
            data[key] = value if rest.endswith("-") else value + "\n"
            continue
        if rest == "":
            sub = {}
            i += 1
            while i < n and lines[i].startswith("  "):
                sm = re.match(r"^  ([A-Za-z_][\w-]*):\s*(.*)$", lines[i])
                if not sm:
                    raise ValueError(f"line {i + 1}: expected nested 'key: value', got {lines[i]!r}")
                sub[sm.group(1)] = _unquote(sm.group(2))
                i += 1
            data[key] = sub
            continue
        data[key] = _unquote(rest)
        i += 1
    return data


def split(path):
    text = Path(path).read_text()
    match = FRONTMATTER.match(text)
    if not match:
        return text, None, None
    return text, match.group(1), match


# ---------------------------------------------------------------- helpers

def rel(path):
    return str(Path(path).resolve().relative_to(REPO_ROOT))


def in_ci():
    return os.environ.get("GITHUB_ACTIONS") == "true"


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


def templates():
    out = {}
    for path in sorted(BLOCKS_DIR.glob("*.md")):
        out[path.stem] = path.read_text().strip()
    if not out:
        sys.exit(f"no block templates found in {rel(BLOCKS_DIR)}")
    return out


def wrap(name, body):
    return f"<!-- block:{name} -->\n{body}\n<!-- /block:{name} -->"


# ---------------------------------------------------------------- check

def check(version):
    errors = []
    tpl = templates()
    for path in skill_files():
        name = rel(path)
        skill_dir = Path(path).parent.name
        text, fm_text, _ = split(path)
        if fm_text is None:
            errors.append(f"{name}: no YAML frontmatter block")
            continue
        try:
            fm = parse_frontmatter(fm_text)
        except ValueError as exc:
            errors.append(f"{name}: frontmatter is not valid ({exc})")
            continue
        for key in ("name", "description", "license"):
            if not fm.get(key):
                errors.append(f"{name}: frontmatter must define {key}")
        if fm.get("name") and fm["name"] != skill_dir:
            errors.append(f"{name}: name {fm['name']!r} != directory name {skill_dir!r}")
        desc = fm.get("description") or ""
        wtu = fm.get("when_to_use") or ""
        if len(desc) > DESCRIPTION_LIMIT:
            errors.append(f"{name}: description is {len(desc)} chars (limit {DESCRIPTION_LIMIT})")
        if len(desc) + len(wtu) > LISTING_LIMIT:
            errors.append(
                f"{name}: description + when_to_use is {len(desc) + len(wtu)} chars "
                f"(Claude Code truncates the listing at {LISTING_LIMIT})"
            )
        skill_version = (fm.get("metadata") or {}).get("version") if isinstance(fm.get("metadata"), dict) else None
        if skill_version is None:
            errors.append(f"{name}: missing metadata.version (expected \"{version}\")")
        elif not re.search(r'^  version: "[^"]+"$', fm_text, re.M):
            errors.append(f"{name}: metadata.version must be a quoted string")
        elif skill_version != version:
            errors.append(
                f"{name}: metadata.version \"{skill_version}\" != plugin version \"{version}\" "
                f"— run scripts/sync-skills.py --write"
            )

        body = text[len(fm_text):]
        if "$CLAUDE_PLUGIN_ROOT" in body.replace("${CLAUDE_PLUGIN_ROOT}", ""):
            errors.append(f"{name}: unbraced $CLAUDE_PLUGIN_ROOT (use ${{CLAUDE_PLUGIN_ROOT}})")
        found = {}
        for m in BLOCK.finditer(body):
            block_name, content = m.group(1), m.group(2)
            if block_name in found:
                errors.append(f"{name}: block '{block_name}' appears more than once")
            found[block_name] = content
            if block_name not in tpl:
                errors.append(f"{name}: block '{block_name}' has no template in {rel(BLOCKS_DIR)}")
            elif content.strip() != tpl[block_name]:
                errors.append(f"{name}: block '{block_name}' drifted from its template — run scripts/sync-skills.py --write")
        if skill_dir not in PRIMITIVES:
            for required in REQUIRED_BLOCKS:
                if required not in found:
                    errors.append(f"{name}: missing required block '{required}'")
    if errors:
        for err in errors:
            print(f"::error::{err}" if in_ci() else f"ERROR: {err}")
        return 1
    print(f"OK: {len(skill_files())} skills at version \"{version}\", blocks in sync")
    return 0


# ---------------------------------------------------------------- write

def write(version):
    tpl = templates()
    changed = []
    for path in skill_files():
        text, fm_text, match = split(path)
        if fm_text is None:
            sys.exit(f"{rel(path)}: no YAML frontmatter block — fix by hand first")
        if re.search(r"^metadata:", fm_text, re.M):
            if re.search(r"^  version: ", fm_text, re.M):
                new_fm = re.sub(r"^  version: .*$", f'  version: "{version}"', fm_text, count=1, flags=re.M)
            else:
                new_fm = re.sub(r"^metadata:$", f'metadata:\n  version: "{version}"', fm_text, count=1, flags=re.M)
        else:
            new_fm = fm_text + f'\nmetadata:\n  version: "{version}"'
        body = text[match.end():]
        new_body = BLOCK.sub(lambda m: wrap(m.group(1), tpl[m.group(1)]) if m.group(1) in tpl else m.group(0), body)
        new_text = f"---\n{new_fm}\n---\n{new_body}"
        if new_text != text:
            Path(path).write_text(new_text)
            changed.append(rel(path))
    if check(version) != 0:
        sys.exit("post-write verification failed — inspect the files above")
    if changed:
        print(f"updated {len(changed)} file(s):")
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
    mode.add_argument("--write", action="store_true", help="stamp versions and re-sync blocks")
    mode.add_argument("--set", metavar="X.Y.Z", help="bump plugin.json, then --write")
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
