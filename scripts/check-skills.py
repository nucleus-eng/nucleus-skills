#!/usr/bin/env python3
"""Validate the skills in this repo.

Seven checks, all of which catch failures that are otherwise silent:

1. Every skill directory holds a SKILL.md whose `name:` matches the
   directory name. A skill that fails this does not load, and nothing
   reports an error — it simply never appears. That bug went unnoticed in
   nucleus-docs for months.
2. No two skills declare the same `name:`.
3. Relative links, and inline-code paths naming a plugin directory, resolve
   to a real file.
4. The marketplace and plugin manifests parse, and every plugin `source`
   resolves to a directory holding its own plugin manifest. A broken
   manifest is the one failure that stops everything installing, and it
   reports nothing useful when it happens.
5. No stray `skills/` directory at the repo root. Skills lived there before
   this repo became a plugin marketplace. A skill left behind at the old
   path merges cleanly and is simply absent from the plugin, with nothing
   reporting an error — the same silent omission this whole repo exists to
   stop. This is an assertion that the old location is gone, not a check of
   its contents, so it costs nothing once true and retires itself.
6. Every name in a skill's `invokes:` frontmatter field resolves to a known
   skill. An invoked skill that was renamed or deleted would silently break
   without this.
7. `invokes:` frontmatter and in-body `> **INVOKE** name` markers stay in
   sync bidirectionally: every declared invocation has a call-site marker,
   and every call-site marker has a declaration. Either direction of drift
   produces a false sense of completeness in the other.

Exit codes: 0 clean, 1 findings, 2 the check could not run.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugins" / "nucleus" / "skills"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
FIELD = re.compile(r"^(name|description):\s*(.+?)\s*$", re.MULTILINE)
INVOKES_BLOCK = re.compile(r"^invokes:\s*\n((?:[ \t]+-[ \t]+\S+[^\n]*\n?)+)", re.MULTILINE)
INVOKES_ITEM = re.compile(r"^[ \t]+-[ \t]+([A-Za-z0-9_-]+)", re.MULTILINE)
INVOKE_MARKER = re.compile(r"^[ \t]*> \*\*INVOKE\*\* `([A-Za-z0-9_-]+)`", re.MULTILINE)
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
# Inline-code paths naming a directory this plugin owns. Narrow on purpose: a
# bare `main.md` usually points at a consumer repo, and so does `scripts/` —
# but `skills/x.md` and `references/x.md` claim to be ours and can be resolved.
# Markdown-link checking misses these entirely, which is how
# `skills/devnote-style-guide.md` survived the move to `references/`.
CODE_PATH = re.compile(r"`((?:skills|references)/[A-Za-z0-9_./-]+\.md)`")
FENCE = re.compile(r"^(?P<fence>```+|~~~+).*?^(?P=fence)", re.DOTALL | re.MULTILINE)
CODE_SPAN = re.compile(r"`+[^`\n]*`+")


def strip_code(text: str) -> str:
    """Blank out fenced blocks and inline code.

    Links inside them are examples and regexes, not references. Newlines are
    kept so nothing downstream cares about line offsets.
    """
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    return CODE_SPAN.sub(blank, FENCE.sub(blank, text))


def frontmatter_fields(text: str) -> dict[str, str] | None:
    match = FRONTMATTER.match(text)
    if match is None:
        return None
    return {k: v for k, v in FIELD.findall(match.group(1))}


def check_skill(directory: Path, findings: list[str], seen: dict[str, Path]) -> None:
    skill_file = directory / "SKILL.md"
    if not skill_file.is_file():
        findings.append(f"{directory.relative_to(ROOT)}: no SKILL.md — this skill cannot load")
        return

    fields = frontmatter_fields(skill_file.read_text(encoding="utf-8"))
    rel = skill_file.relative_to(ROOT)
    if fields is None:
        findings.append(f"{rel}: no YAML frontmatter — this skill cannot load")
        return

    name = fields.get("name")
    if name is None:
        findings.append(f"{rel}: frontmatter has no `name:` field — this skill cannot load")
    elif name != directory.name:
        findings.append(f"{rel}: `name: {name}` does not match directory `{directory.name}`")
    else:
        first = seen.get(name)
        if first is not None:
            findings.append(f"{rel}: duplicate `name: {name}`, already declared by {first}")
        else:
            seen[name] = rel

    if not fields.get("description"):
        findings.append(f"{rel}: frontmatter has no `description:` — the model cannot decide to load it")


def parse_invokes(frontmatter_text: str) -> list[str]:
    """Extract skill names from an invokes: list in frontmatter text."""
    m = INVOKES_BLOCK.search(frontmatter_text)
    if m is None:
        return []
    return INVOKES_ITEM.findall(m.group(0))


def check_invokes(directory: Path, seen: dict[str, Path], findings: list[str]) -> None:
    """Verify every name in invokes: resolves to a known skill, and that
    invokes: declarations and in-body INVOKE markers stay in sync."""
    skill_file = directory / "SKILL.md"
    if not skill_file.is_file():
        return  # already flagged by check_skill
    raw = skill_file.read_text(encoding="utf-8")
    fm = FRONTMATTER.match(raw)
    if fm is None:
        return
    rel = skill_file.relative_to(ROOT)

    declared = parse_invokes(fm.group(1))

    # Check 6: every declared name resolves to a real skill.
    for name in declared:
        if name not in seen:
            findings.append(
                f"{rel}: `invokes: {name}` — no skill with this name exists"
            )

    # Check 7: bidirectional sync between invokes: and INVOKE markers.
    # Strip fenced blocks only (not inline code spans): fenced blocks may
    # contain example INVOKE markers that are documentation, not call sites.
    # Inline code spans must NOT be stripped — they contain the skill name
    # that the regex needs to capture (e.g. `devstudio-read-from-google-drive`).
    body = FENCE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw[fm.end():])
    marked = set(INVOKE_MARKER.findall(body))
    declared_set = set(declared)

    for name in sorted(declared_set - marked):
        findings.append(
            f"{rel}: `invokes: {name}` declared but no `> **INVOKE** \\`{name}\\`` marker in body"
        )
    for name in sorted(marked - declared_set):
        if name in seen:  # only flag markers that point at real skills
            findings.append(
                f"{rel}: INVOKE marker for `{name}` in body but not declared in `invokes:`"
            )


def check_links(path: Path, findings: list[str]) -> None:
    raw = path.read_text(encoding="utf-8")
    plugin_root = ROOT / "plugins" / "nucleus"
    for target in sorted(set(CODE_PATH.findall(raw))):
        # Either plugin-root-relative or relative to the file that names it.
        if not ((plugin_root / target).exists() or (path.parent / target).exists()):
            findings.append(f"{path.relative_to(ROOT)}: names a plugin path that does not exist — {target}")

    text = strip_code(raw)
    for target in MD_LINK.findall(text):
        target = target.split("#", 1)[0].split(" ", 1)[0].strip()
        if not target or "://" in target or target.startswith(("#", "mailto:")):
            continue
        resolved = (ROOT if target.startswith("/") else path.parent) / target.lstrip("/")
        if not resolved.exists():
            findings.append(f"{path.relative_to(ROOT)}: link target does not exist — {target}")


def check_manifests(findings: list[str]) -> None:
    """Validate the marketplace catalog and every plugin it lists."""
    if not MARKETPLACE.is_file():
        findings.append(
            f"{MARKETPLACE.relative_to(ROOT)} is missing — without it no repo can "
            f"subscribe to this marketplace"
        )
        return

    try:
        catalog = json.loads(MARKETPLACE.read_text())
    except json.JSONDecodeError as exc:
        findings.append(f"{MARKETPLACE.relative_to(ROOT)}: invalid JSON — {exc}")
        return

    for field in ("name", "owner", "plugins"):
        if field not in catalog:
            findings.append(f"{MARKETPLACE.relative_to(ROOT)}: no `{field}` field")

    for entry in catalog.get("plugins", []):
        name = entry.get("name", "<unnamed>")
        source = entry.get("source")
        if not isinstance(source, str):
            # Non-local sources (github, url, git-subdir) cannot be checked here.
            continue
        directory = (ROOT / source).resolve()
        if not directory.is_dir():
            findings.append(f"marketplace plugin `{name}`: source does not exist — {source}")
            continue
        manifest = directory / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            findings.append(f"marketplace plugin `{name}`: no .claude-plugin/plugin.json in {source}")
            continue
        try:
            plugin = json.loads(manifest.read_text())
        except json.JSONDecodeError as exc:
            findings.append(f"{manifest.relative_to(ROOT)}: invalid JSON — {exc}")
            continue
        if plugin.get("name") != name:
            findings.append(
                f"{manifest.relative_to(ROOT)}: `name: {plugin.get('name')}` does not match "
                f"the marketplace entry `{name}`"
            )


def main() -> int:
    if not SKILLS.is_dir():
        print(f"error: {SKILLS.relative_to(ROOT)} does not exist", file=sys.stderr)
        return 2

    findings: list[str] = []
    seen: dict[str, Path] = {}

    check_manifests(findings)

    stray = ROOT / "skills"
    if stray.is_dir():
        names = sorted(d.name for d in stray.iterdir() if d.is_dir())
        listed = ", ".join(names) if names else "no skill directories"
        findings.append(
            f"skills/ still exists at the repo root ({listed}) — skills live in "
            f"plugins/nucleus/skills/ and anything here ships in no plugin"
        )

    directories = sorted(d for d in SKILLS.iterdir() if d.is_dir())
    if not directories:
        print(f"error: no skill directories under {SKILLS.relative_to(ROOT)}", file=sys.stderr)
        return 2

    for directory in directories:
        check_skill(directory, findings, seen)

    # Second pass: invokes: validation needs seen to be fully populated first.
    for directory in directories:
        check_invokes(directory, seen, findings)

    for markdown in sorted((ROOT / "plugins").rglob("*.md")):
        check_links(markdown, findings)

    if findings:
        print(f"⛔️ {len(findings)} finding(s):\n")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print(f"✅ manifests valid, {len(directories)} skills, all loadable, no duplicate names, links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
