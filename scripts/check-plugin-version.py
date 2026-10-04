#!/usr/bin/env python3
"""Fail a change to the plugin that does not move the plugin's version.

WHY THIS EXISTS, MEASURED 2026-10-04. `plugins/nucleus/.claude-plugin/plugin.json`
has read `"version": "0.1.0"` since the file was written. Two commits have ever
touched it and its whole history contains one `+ "version"` line.

THAT STRING IS BOTH THE UPDATE CHECK AND THE CACHE KEY. An install lands in
`~/.claude/plugins/cache/nucleus/nucleus/<version>/`, so every version of the
content shares one directory, and `claude plugin update` compares the installed
version against the published one and finds them equal. The update is a no-op
and reports success.

WHAT IT COST. On 2026-10-04 an installed copy recorded `gitCommitSha af8ebb6`
from 2026-09-29 while `main` was 30 commits ahead. In between, `staging/SKILL.md`
changed by 42 lines — the skill that governs how every session in this workspace
makes a staged edit — and `glossary.md` by 15. Sessions ran five-day-old rules
while the updater said they were current. An uninstall and reinstall was the only
way anyone found to move it.

SO THIS CHECKS ONE THING: if a pull request changes anything under
`plugins/nucleus/`, the plugin's `version` must differ from the base branch's.
It does not check that the bump is semantically right, only that it moved. A
wrong bump is visible in review; a missing one is not visible anywhere.

HOW TO PICK THE NEW NUMBER. The plugin tracks the Nucleus Distribution's
minor version, which `nucleus-docs` badges on its front page: at the time of
writing that reads v0.6.0, so this plugin reads 0.6.0 too.

  - A routine change -- a skill edited, added or removed -- increments the
    LAST digit by one. 0.6.0 becomes 0.6.1, then 0.6.2. Do not skip numbers
    and do not reuse one.
  - The MIDDLE digit moves only when the Distribution's does, and it moves to
    whatever the Distribution now reads, with the last digit back to 0.
  - The FIRST digit is the Distribution's to move, not this repo's.

The reason the last digit must move every time is above: it is the cache key.
A change shipped without one is a change nobody receives.

AND IT IS WRITTEN TWICE. `.claude-plugin/marketplace.json` carries its own copy,
which is what a consumer reads before installing. Both must move together, and
this script fails a pull request where they disagree.

    python3 scripts/check-plugin-version.py              # against origin/main
    python3 scripts/check-plugin-version.py --base <ref>
"""
import argparse
import json
import subprocess
import sys

PLUGIN = "plugins/nucleus"
MANIFEST = f"{PLUGIN}/.claude-plugin/plugin.json"
MARKETPLACE = ".claude-plugin/marketplace.json"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def version_at(ref: str) -> str | None:
    """The plugin version at `ref`, or None when the manifest is absent there."""
    blob = git("show", f"{ref}:{MANIFEST}")
    if not blob:
        return None
    try:
        return json.loads(blob).get("version")
    except json.JSONDecodeError:
        return None


def marketplace_version() -> str | None:
    """The version the marketplace entry advertises for this plugin, at HEAD.

    THE VERSION IS WRITTEN TWICE AND ONLY ONE COPY WAS EVER CHECKED. Found in
    review of this change: `plugin.json` read 0.2.0 while `marketplace.json`
    still read 0.1.0, and `check-skills.py` -- which says the two manifests
    "agree" -- contains no mention of `version` at all. A consumer reads the
    marketplace entry, so a plugin bumped in one file and not the other is
    advertised at the old number.
    """
    try:
        doc = json.loads(open(MARKETPLACE).read())
    except (OSError, json.JSONDecodeError):
        return None
    for entry in doc.get("plugins") or []:
        if entry.get("source", "").rstrip("/").endswith(PLUGIN.split("/")[-1]):
            return entry.get("version")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="origin/main", help="branch to compare against")
    args = ap.parse_args()

    base = git("merge-base", args.base, "HEAD")
    if not base:
        print(f"error: cannot find a merge base with {args.base}. "
              "A shallow checkout cannot answer this; fetch with depth 0.",
              file=sys.stderr)
        return 2

    changed = [p for p in git("diff", "--name-only", base, "HEAD").splitlines()
               if p.startswith(PLUGIN + "/")]
    if not changed:
        print(f"✅ nothing under {PLUGIN}/ changed; the version need not move.")
        return 0

    before, after = version_at(base), version_at("HEAD")
    if after is None:
        print(f"⛔️ {MANIFEST} is missing or unparseable at HEAD.", file=sys.stderr)
        return 1

    if before == after:
        others = [p for p in changed if p != MANIFEST]
        print(f"⛔️ {len(changed)} file(s) under {PLUGIN}/ changed and the version "
              f"stayed at {after}.", file=sys.stderr)
        for p in others[:10]:
            print(f"     {p}", file=sys.stderr)
        if len(others) > 10:
            print(f"     …and {len(others) - 10} more", file=sys.stderr)
        print(f"\n   The version is the install cache key, so a release that does not "
              f"move it\n   is a release nobody receives. Bump `version` in {MANIFEST}.",
              file=sys.stderr)
        return 1

    market = marketplace_version()
    if market != after:
        print(f"⛔️ the version is written twice and the two disagree:\n"
              f"     {MANIFEST}  {after}\n"
              f"     {MARKETPLACE}  {market}", file=sys.stderr)
        print(f"\n   A consumer reads the marketplace entry, so the plugin would be "
              f"advertised\n   at {market} whatever {MANIFEST} says. Move both.",
              file=sys.stderr)
        return 1

    print(f"✅ {len(changed)} file(s) under {PLUGIN}/ changed and the version moved "
          f"{before} → {after}, in both manifests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
