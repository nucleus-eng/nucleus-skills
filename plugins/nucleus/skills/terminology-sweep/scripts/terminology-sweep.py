#!/usr/bin/env python3
"""
terminology-sweep.py — flag terminology drift across a docs corpus.

Three detection tiers, deliberately distinguished because confidence differs:

  ERROR   — an exact wrong string. Mechanically certain. Fails the run.
  SUSPECT — a co-occurrence that is very likely wrong but needs a human to
            confirm, because the fix may need someone else's consent.
  REVIEW  — a term that MAY be collapsing a distinction. High false-positive
            rate by design; counted and listed for triage, never called an error.

Only tier 1 fails by default. Tiers 2 and 3 exist to be read, not to gate, and
a check that blocks on them trains people to ignore it.

The rules live in a config file, not in this script. What the machinery does is
generic; which words are wrong is a per-repo decision that changes as a project
renames things.

Usage:
    terminology-sweep.py                          # sweep docs/, report to stdout
    terminology-sweep.py docs/modules             # sweep a subtree
    terminology-sweep.py --out report.md          # write the report to a file
    terminology-sweep.py --config path/to.toml    # non-default config location
    terminology-sweep.py --strict                 # also fail on SUSPECT

Exit codes:
    0  no ERROR (and, with --strict, no SUSPECT)
    1  findings that should block
    2  the check could not run (missing config, bad regex, no git repo)
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    sys.exit("terminology-sweep needs Python 3.11+ for tomllib")

DEFAULT_CONFIG = "terminology.toml"
SKILL_DEFAULT = Path(__file__).resolve().parent.parent / "references" / "terminology.example.toml"


def repo_root():
    """The docs repository, from the working directory.

    This script is distributed as part of a skill and runs against whatever repo
    invoked it, so the root can never come from `__file__`.
    """
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if out.returncode:
        sys.exit(2)
    return Path(out.stdout.strip())


def load_config(repo, explicit):
    """Config from --config, else <repo>/terminology.toml, else the shipped example.

    An explicit --config that does not exist is an error, not a fallback. Silently
    sweeping with different rules than the caller asked for is how a clean exit
    code stops meaning anything.
    """
    if explicit and not Path(explicit).is_file():
        print(f"--config not found: {explicit}", file=sys.stderr)
        sys.exit(2)
    for candidate, label in ((explicit, "--config"),
                             (repo / DEFAULT_CONFIG, "repo"),
                             (SKILL_DEFAULT, "skill default")):
        if candidate and Path(candidate).is_file():
            with open(candidate, "rb") as fh:
                return tomllib.load(fh), Path(candidate), label
    print(f"no config found: pass --config, or add {DEFAULT_CONFIG} at the repo root",
          file=sys.stderr)
    sys.exit(2)


def compile_or_die(pattern, where):
    try:
        return re.compile(pattern, re.IGNORECASE if pattern.islower() else 0)
    except re.error as exc:
        print(f"bad regex in {where}: {pattern!r} — {exc}", file=sys.stderr)
        sys.exit(2)


def tracked_md(repo, paths):
    """Committed .md and .csv files under the given paths.

    Tracked-only on purpose: build artifacts under `generated/` are gitignored,
    and sweeping them reports the same drift several times over.
    """
    out = subprocess.run(["git", "-C", str(repo), "ls-files", *paths],
                         capture_output=True, text=True, check=True)
    return [repo / p for p in out.stdout.splitlines()
            if p.endswith((".md", ".csv")) and "/generated/" not in p]


def sweep(repo, files, cfg):
    errors, suspects = [], []
    review = defaultdict(lambda: defaultdict(list))
    framework = defaultdict(lambda: defaultdict(int))

    error_rules = [(compile_or_die(r["pattern"], "errors"), r) for r in cfg.get("errors", [])]

    suspect_rules = []
    for r in cfg.get("suspects", []):
        suspect_rules.append({
            "name": r.get("name", "unnamed"),
            "trigger": compile_or_die(r["trigger"], "suspects.trigger"),
            "match": compile_or_die(r["match"], "suspects.match"),
            "require": compile_or_die(r["require"], "suspects.require") if r.get("require") else None,
            "veto": compile_or_die(r["veto"], "suspects.veto") if r.get("veto") else None,
            "min_value": r.get("min_value"),
            "why": r.get("why", ""),
        })

    review_rules = [(r.get("name", "unnamed"), compile_or_die(r["pattern"], "review"))
                    for r in cfg.get("review", [])]
    framework_terms = cfg.get("framework", {}).get("terms", [])

    for f in files:
        rel = f.relative_to(repo)
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        text = "\n".join(lines)

        # Tier 1 — exact wrong strings.
        for pat, rule in error_rules:
            for i, line in enumerate(lines, 1):
                for m in pat.finditer(line):
                    errors.append((rel, i, m.group(0), rule.get("correct", ""),
                                   rule.get("why", "")))

        # Tier 2 — co-occurrence. The file-level trigger says the rule is
        # relevant here at all; require/veto then decide line by line whether
        # the candidate carries the meaning the rule cares about.
        for r in suspect_rules:
            if not r["trigger"].search(text):
                continue
            for i, line in enumerate(lines, 1):
                if r["require"] and not r["require"].search(line):
                    continue
                if r["veto"] and r["veto"].search(line):
                    continue
                for m in r["match"].finditer(line):
                    if r["min_value"] is not None:
                        digits = next((g for g in m.groups() if g and g.isdigit()), None)
                        if digits is None or int(digits) < r["min_value"]:
                            continue
                    suspects.append((rel, i, m.group(0), r["name"], r["why"]))

        # Tier 3 — terms to count and list for human triage.
        for name, pat in review_rules:
            for i, line in enumerate(lines, 1):
                if pat.search(line):
                    review[name][rel].append((i, line.strip()[:110]))

        for term in framework_terms:
            n = len(re.findall(rf"\b{re.escape(term)}\b", text))
            if n:
                framework[rel][term] = n

    return errors, suspects, review, framework


def report(errors, suspects, review, framework, files, cfg, cfg_path, cfg_label):
    L = []
    add = L.append
    add("# Terminology sweep\n")
    add(f"Swept {len(files)} tracked file(s). Rules from `{cfg_path}` ({cfg_label}).\n")

    if cfg.get("glossary"):
        add("## Glossary applied\n")
        add("| Term | Means | Notes |")
        add("| --- | --- | --- |")
        for g in cfg["glossary"]:
            add(f"| {g.get('term','')} | {g.get('means','')} | {g.get('notes','')} |")
        add("")

    add("## ERROR — exact wrong strings\n")
    if errors:
        add("| File | Line | Found | Should be | Why |")
        add("| --- | --- | --- | --- | --- |")
        for rel, i, found, correct, why in errors:
            add(f"| `{rel}` | {i} | `{found}` | `{correct}` | {why} |")
        add(f"\n**{len(errors)} occurrence(s).**")
    else:
        add("None.")

    add("\n## SUSPECT — needs human confirmation\n")
    add("Not auto-fixable. A rename here may need someone else's consent.\n")
    if suspects:
        add("| File | Line | Found | Rule | Concern |")
        add("| --- | --- | --- | --- | --- |")
        seen = set()
        for rel, i, found, name, why in suspects:
            key = (rel, i, found)
            if key in seen:
                continue
            seen.add(key)
            add(f"| `{rel}` | {i} | `{found}` | {name} | {why} |")
        add(f"\n**{len(seen)} occurrence(s).**")
    else:
        add("None.")

    add("\n## REVIEW — possible collapsed distinctions\n")
    add("High false-positive rate by design. Counts first, then locations.\n")
    if review:
        add("| Term | Files | Lines |")
        add("| --- | --- | --- |")
        for name in review:
            add(f"| `{name}` | {len(review[name])} | {sum(len(v) for v in review[name].values())} |")
        for name, files_map in review.items():
            add(f"\n### `{name}`\n")
            for rel in sorted(files_map, key=str):
                hits = files_map[rel]
                add(f"- `{rel}` — {len(hits)} line(s): "
                    + ", ".join(str(i) for i, _ in hits[:20])
                    + (" …" if len(hits) > 20 else ""))
    else:
        add("No review terms configured.")

    terms = cfg.get("framework", {}).get("terms", [])
    if terms and framework:
        add("\n## Framework-term usage\n")
        add("Counts only. A high count is not a violation — this is a map of where "
            "to check that each term carries its defined sense rather than a loose "
            "English one. Not mechanically decidable.\n")
        add("| File | " + " | ".join(terms) + " |")
        add("| --- |" + " --- |" * len(terms))
        for rel in sorted(framework, key=str):
            row = framework[rel]
            add(f"| `{rel}` | " + " | ".join(str(row.get(t, "")) for t in terms) + " |")

    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=None,
                    help="paths to sweep (default: docs/)")
    ap.add_argument("--config", help=f"rules file (default: <repo>/{DEFAULT_CONFIG})")
    ap.add_argument("--out", help="write the report here instead of stdout")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on SUSPECT findings")
    args = ap.parse_args()

    repo = repo_root()
    cfg, cfg_path, cfg_label = load_config(repo, args.config)
    paths = args.paths or ["docs/"]
    files = tracked_md(repo, paths)
    if not files:
        print(f"no tracked .md or .csv files under {paths}", file=sys.stderr)
        return 2

    errors, suspects, review, framework = sweep(repo, files, cfg)
    out = report(errors, suspects, review, framework, files, cfg, cfg_path, cfg_label)

    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8")
    else:
        print(out)

    n_suspect = len({(r, i, f) for r, i, f, _, _ in suspects})
    summary = (f"swept {len(files)} file(s): "
               f"{len(errors)} ERROR, {n_suspect} SUSPECT, "
               f"{sum(len(v) for d in review.values() for v in d.values())} REVIEW")
    print(summary, file=sys.stderr)

    if errors:
        return 1
    if args.strict and n_suspect:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
