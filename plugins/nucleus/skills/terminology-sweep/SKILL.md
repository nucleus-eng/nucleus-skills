---
name: terminology-sweep
description: Sweep a docs corpus for terminology drift — renamed terms that survive in old pages, acronyms collapsed into a vague umbrella word, and project-defined words used in their loose English sense. Use when a term has been renamed and the rename needs propagating, when auditing a tranche of pages before review, when setting up a terminology gate in CI, or when asked to check that docs use agreed vocabulary consistently. Covers the three-tier confidence model, how to write a co-occurrence rule that is not mostly noise, and which findings may be fixed mechanically.
---

# Terminology sweep

Renames leak. A term gets changed, the pages written that week use the new word,
the pages written last month keep the old one, and nothing notices — spelling
tools do not know your project's vocabulary, and prose linters check style, not
whether "vesicle" was supposed to become "liposome".

This skill sweeps a corpus for that drift. What it is *not* is a spell checker or
a style linter: it looks only for words this project has made decisions about.

## The one rule that matters

**Sort findings by how certain you are, and gate only on the certain ones.**

| Tier | What it is | Certainty | Gates? |
| --- | --- | --- | --- |
| ERROR | An exact wrong string | mechanical | **yes** |
| SUSPECT | A co-occurrence that is probably wrong | needs a human | no |
| REVIEW | A term that *may* collapse a distinction | mostly fine | no |

A check that blocks on doubtful findings gets ignored, and then it stops catching
the certain ones too. Keep ERROR small and unarguable: every rule in it should be
a rename that is already decided, never a preference still under discussion.

`--strict` promotes SUSPECT to blocking. That is for a local pre-review pass, not
for CI.

## Running it

```bash
python3 scripts/terminology-sweep.py                       # sweep docs/, report to stdout
python3 scripts/terminology-sweep.py docs/modules           # one subtree
python3 scripts/terminology-sweep.py --out tmp/sweep.md     # report to a file
python3 scripts/terminology-sweep.py --strict               # also fail on SUSPECT
```

Exit codes: `0` clean · `1` blocking findings · `2` the check could not run
(missing config, bad regex, not a git repo). The third is separate on purpose —
tooling breakage must not read as clean docs.

Tracked files only, so gitignored build output under `generated/` is skipped.
Sweeping it reports the same drift several times over.

## Rules live in config, not in the script

The machinery is generic; which words are wrong is a per-repo decision that
changes every time a project renames something. Rules go in `terminology.toml` at
the repo root. `references/terminology.example.toml` is a worked starting point —
copy it and edit.

**Do not hardcode a project's vocabulary into the script.** Same reason a Vale
rule file is data: the person who renames a term should be able to update the
check without reading Python.

## Writing a tier-2 rule that is not mostly noise

A co-occurrence rule has four parts, and the last two are what make it usable:

```toml
[[suspects]]
name      = "suv-size"
trigger   = '\bSUVs?\b'                  # rule applies to this file at all
match     = '\b(\d{2,4})\s*nm\b'         # the candidate token, per line
require   = '\b(diameter|extrud\w*|…)\b' # semantic confirmation, same line
veto      = '\b(absorb\w*|wavelength|…)\b' # semantic exclusion, same line
min_value = 100
why       = "page says SUV but states a particle size >=100 nm"
```

`require` and `veto` are not polish. **The first version of that rule had
neither.** It flagged every `<N> nm` on any page mentioning SUV, and 24 of its 28
hits were wavelengths — 570 nm CPRG absorbance, 405 nm PEGDA crosslinking — read
as particle sizes. Adding the pair took it to 3 hits, all genuine.

A tier-2 rule without semantic context is a tier-3 rule wearing a costume. If you
cannot write a `require` for it, put it in `[[review]]` and let a human skim.

## Reading the output

**ERROR** — fix mechanically. When scripting the fix, watch for the substitution
hazards below.

**SUSPECT** — read each one. These are the findings most likely to need someone
else's agreement: a size-class rename can require the collaborator who generated
the data to confirm what they actually made. Report and wait; do not fix.

**REVIEW** — skim the counts, not every line. A falling count across runs is the
signal. In the corpus this was built for, `bare-vesicle` went from 106 lines to
5 after a rename, and all 5 survivors were legitimate: two inside direct quotes
from a source document, three in acronym expansions ("small unilamellar
vesicle"). **That is a healthy tier-3 result, not a backlog.** Quoted source text
and acronym expansions are meant to keep the old word.

### Every tier-3 rule is temporary

A term belongs in `[[review]]` while it is either **being retired** (the count
should fall toward zero) or **under active decision** (you want every use listed
before ruling on it). **When a term is ruled in, delete its rule.**

Skip that step and the rule starts counting correct usage. The count then *climbs
as the rename succeeds*, and the tier fills with noise that buries the rules still
doing work. Measured: leaving two ruled-in terms in `[[review]]` produced 345 of
370 hits, every one of them correct, while the two rules that mattered accounted
for 25. A reviewer looking at "370 to review" reasonably concludes the check is
broken — and stops reading it.

So a rising tier-3 count means one of two things, and they are opposite: drift is
getting worse, or a rule has outlived its decision. Check which before acting.

**Framework-term map** — counts per file for words that have a defined technical
sense in your project *and* an ordinary English sense (Composition, Function,
Requirements, Module…). Whether a given use carries the defined sense is not
mechanically decidable, so this is a map of where to look, never a list of
violations.

## Substitution hazards

Every one of these has broken something in practice.

- **Never substitute into an identifier.** A term sweep that replaced a word
  inside Mermaid node ids broke two diagrams silently — the ids contained the
  prose string, and the replacement introduced a space. Restrict replacements to
  prose, and re-render or re-check anything generated afterwards.
- **Leave quoted source text alone.** If a page quotes a document, the quote keeps
  the document's wording. Changing it misrepresents the source.
- **Leave acronym expansions alone.** "Small unilamellar vesicle" is what SUV
  stands for. The rename applies to the umbrella use, not the expansion.
- **Guard against URL encoding.** `%2C` and friends contain letters and digits
  that patterns match. Use a negative lookbehind for `%` in any numeric
  substitution.
- **Check for a same-name file elsewhere.** Renaming a term often implies renaming
  a directory, a TOC entry, and an index row. The sweep finds prose; it does not
  find the sidebar.

## Checklist

- [ ] Rules are in `terminology.toml`, not in the script
- [ ] Every ERROR rule is a decided rename, not an open preference
- [ ] Every SUSPECT rule has a `require`, and a `veto` if the token is ambiguous
- [ ] The report was read, not just the exit code
- [ ] SUSPECT findings that need someone else's consent are reported, not fixed
- [ ] After any substitution: identifiers, quotes, and acronym expansions checked
- [ ] Generated content re-generated and re-checked
