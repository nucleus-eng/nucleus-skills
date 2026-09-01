---
name: lint-docs
description: Run and interpret the nucleus-docs quality tools — Vale, codespell, lychee, and the strict MyST build. Use before opening a PR or committing content, and whenever one of those tools reports an error you need to interpret, fix, or justify suppressing.
---

### Prose linting (Vale)

**Run `git ls-files docs/ | grep -E '\.(md|csv)$' | xargs vale` before opening a PR or committing a content migration.** This command lints only committed source files (skipping gitignored `generated/` artifacts). Vale lints both `.md` and `.csv` files and runs as part of the `qa` CI workflow (`.github/workflows/qa.yml`).

```bash
git ls-files docs/ | grep -E '\.(md|csv)$' | xargs vale          # lint all committed docs (skips generated/)
vale --glob='!**/generated/**' docs/                              # lint full docs/ tree, excluding generated/
vale <file.md>                                                     # lint a single file
```

Vale rules live in `styles/nucleus/`. Current rules enforce temperature unit formatting (`°C`), micro symbol usage (`µ`), chemical notation (subscripts and ion superscripts), and unit spacing. Executable tests for these rules live in `tests/` (pytest, not content — run `python -m pytest` from the repo root).

**Interpreting temperature-related errors.** Temperature formatting is enforced by two overlapping rules: `nucleus.units` flags spelled-out forms (`degC`, `degrees C`, `degrees Celsius`, `deg C`) via substitution; `nucleus.degrees-symbol` flags bare digit+C patterns (`95C`, `72 C`) via a raw regex. Both fire as `error` level. In practice, `nucleus.degrees-symbol` currently has a known detection gap — bare `\d+C` patterns are not reliably detected (tracked by `vale-miss` annotations in `styles/tests/temperature.md`). Rely on `nucleus.units` for spelled-out forms; flag bare patterns manually until the gap is fixed.

**Interpreting `nucleus.degrees-symbol` errors.** When Vale flags a `nucleus.degrees-symbol` error, check the surrounding context:

- **Real error** — the token is a temperature value. Fix it by adding the degree symbol (e.g., `37C` → `37 °C`, `4 C` → `4 °C`).
  - Signals: preceded by "at", "to", "of", or a verb like "incubate", "store", "heat"; followed by "for X minutes/hours"; in a reaction table or thermocycler step.
  - **Table cells**: a bare value (e.g., `37C`) in a table column whose header indicates temperature (e.g., "Temperature", "Incubation temp", "Storage") is always a real error, even without surrounding signal words.
- **False positive** — the token is a label, not a temperature. Leave it alone.
  - Signals: preceded by "Figure", "Fig.", "Step", "Lane", "Panel", "Tube", "Option", or a similar structural label word.

**Interpreting `nucleus.chemical-notation` errors.** This rule flags molecular formulae and wavelength labels written with bare ASCII digits and suggests the correct Unicode subscript form. Always a real error — replace `OD600` → `OD₆₀₀`, `A260` → `A₂₆₀`, `H2O` → `H₂O`, `ddH2O` → `ddH₂O`, `MgSO4` → `MgSO₄`, etc. The rule is a substitution rule — the error message shows the exact correct form to use. There are no known false positives (the rule uses an explicit curated list of formulae rather than a generic pattern, so construct names like `pET28a` and labels like `A19` are unaffected).

**Interpreting `nucleus.ion-charges` errors.** This rule flags ion charges written with inline numbers rather than Unicode superscripts. Always a real error — replace `Mg2+` → `Mg²⁺`, `Ni2+` → `Ni²⁺`, `Na+` → `Na⁺`, `K+` → `K⁺`, `Mg++` → `Mg²⁺`, etc. Superscript characters: ⁺ (U+207A), ² (U+00B2), ³ (U+00B3).

**Interpreting `nucleus.micro-symbol` errors.** This rule flags patterns like `10 uL`, `500 uM`, or `2 um` that use an ASCII `u` instead of the micro symbol `µ`. Always a real error — replace with `µL`, `µM`, or `µm` respectively.

**Vale `TokenIgnores` limitation on CSV files.** Vale's `TokenIgnores` setting (used to suppress URL matches) works for `.md` files but is silently ignored for `.csv` files. This means URL-encoded sequences like `%2C` in CSV cells can trigger rules even when URLs are listed in `TokenIgnores`. The workaround is to bake URL safety directly into the rule pattern (e.g., `(?<!%)\d+\s*C\b` instead of `\d+\s*C\b`).

**Applying fixes programmatically.** When using a script (e.g., perl/sed) to bulk-apply degrees-symbol fixes, always use a negative lookbehind for `%` to avoid corrupting URL-encoded sequences like `%2C` (comma):

```perl
# Safe — won't corrupt %2C, %3C, etc. in URLs
s/(?<!%)(\d+)C\b/$1°C/g

# Unsafe — will corrupt URL-encoded sequences
s/(\d+)C\b/$1°C/g
```

Do not add Vale inline suppression comments (`<!-- vale off -->`) without confirming with the developer first. When suppressing only a specific rule (e.g., to silence BOM product-name false positives), prefer rule-scoped suppression over a blanket `<!-- vale off -->`:

```html
<!-- vale nucleus.magnitude-unit-spacing = NO -->
:::{table} Bill of Materials
...
:::
<!-- vale nucleus.magnitude-unit-spacing = YES -->
```

Additionally, some rules (e.g., nucleus.range-styles) will require unit consistency which may require negative lookbehinds, capture groups, and semantic parsing in extreme cases (e.g., 50-2000 ng/mL -> 50 ng/mL to 2000 ng/mL, equivlant to 50 ng/mL to 2 ug/mL). Perl scripts will often generate errors that Vale does not catch (e.g., 50-2000 ng/mL -> 50 ng to 2000 ng/mL; inconsistent units). Before applying changes like these repo-wide, assess how complicated the search-and-replace job is and whether simple regex will suffice. After making such changes, cherry pick a few example substitutions and check for semantic correctness (e.g., consistent units).

**Canonical unit list.** Several Vale rules share an overlapping set of recognised units. Vale rule files are self-contained YAML and have no native include or variable mechanism, so the lists are duplicated by design — the rules differ slightly because false-positive risk varies by context. The canonical reference list (for human consistency checks, not machine enforcement) is:

| Domain | Units |
| --- | --- |
| Length | `nm`, `µm`, `mm`, `cm`, `km` |
| Volume | `nL`, `µL`, `mL`, `L` |
| Mass | `µg`, `mg`, `g`, `kg` |
| Concentration | `nM`, `µM`, `mM`, `M` |
| Molecular weight | `Da`, `kDa` |
| Time | `s`, `min`, `h`, `d` (SI); `yr`, `mo` (non-SI, no SI symbol exists) |
| Centrifugation | `rcf`, `rpm` |
| Temperature | `°C` |

When adding a new unit to one rule, check whether the other rules (magnitude-unit-spacing, range-style, thousands-separator) should also be updated.

**Known NIST SP 811 divergences.** The following are deliberate departures from NIST SP 811, documented here so they read as decisions rather than oversights:

| NIST rule | NIST says | Our style | Rationale |
| --- | --- | --- | --- |
| §7.10.2 — percent | `25 %` (space before `%`) | `25%` | Universal convention; `25 %` reads as unusual to bench scientists |
| §7.10.3 — ppm/ppb/ppt | Not acceptable; use `µL/L` etc. | `ppm` permitted, as is `µL/L` etc.| Accessible shorthand; rarely appears in docs |
| Time abbreviations | `h`, `min`, `s`, `d` | `yr`, `mo` also used | Year and month have no SI symbol; `yr`/`mo` are the accepted non-SI forms |

### Spell checking (codespell)

**Run `codespell docs/` before opening a PR or committing content.** codespell catches real typos and enforces American English spelling.

```bash
codespell docs/          # check all docs
codespell <file.md>      # check a single file
```

Configuration lives in `.codespellrc` at the repo root. It uses the `en-GB_to_en-US` builtin dictionary, which flags British spellings as errors (`labelled` → `labeled`, `grey` → `gray`, `Acknowledgements` → `Acknowledgments`, `homogenous` → `homogeneous`). The `ignore-words = .codespell-ignore` option suppresses known false positives — add a **lowercased** word on its own line to suppress it (e.g., `ser` suppresses the amino acid abbreviation Ser which codespell misreads as a typo for "set").

codespell only flags words in its curated misspelling dictionary, so niche technical terms (`PURExpress`, `plamGFP`, `PURET7`) are not flagged.

### Link checking (lychee)

**Run `python3 scripts/check-links.py docs/` before opening a PR if you have added, edited, or removed any links or URLs.** Takes ~20 s for the whole corpus.

```bash
python3 scripts/check-links.py docs/                  # both passes over all docs
python3 scripts/check-links.py <file.md>              # both passes, one file
python3 scripts/check-links.py --offline-only docs/   # internal links only, no network (~0.05 s)
```

The script wraps `lychee` and runs two passes: an **offline pass** over internal/relative links, and a **network pass** over external URLs. Exit codes are `0` (nothing blocking), `1` (broken links), `2` (the check could not run — e.g. lychee missing; distinct so tooling breakage isn't mistaken for broken docs).

**A failure is judged by what it says about the link, not by which vendor served it.** Do not add vendor domains or status codes to a suppression list — there isn't one, deliberately (issues #193, #199).

| Signal | Verdict |
| --- | --- |
| HTTP 404 or 410 | **blocking** — the resource is gone |
| Hostname does not resolve | **blocking** — typo'd or dead domain |
| Relative/root-relative link resolves to no file | **blocking** — this 404s the deployed site |
| HTTP 401, 403, 429, any 5xx | tolerated, reported — crawler refused or server hiccup |
| Any other 4xx (400, 405, 406, 451…) | tolerated, reported — bot-shaped rejection |
| Timeout, TLS error, HTTP/2 reset, connection reset | tolerated, reported — says nothing about link validity |

Tolerated failures are normal and expected: a clean run currently reports ~120 of them (Sigma-Aldrich and Cytiva reset HTTP/2 connections; many vendors and `doi.org` return 403 to crawlers). **`✅ no broken links` alongside a long tolerated list is a pass.**

**Blame partitioning.** In CI the check runs with `--blame-changed <base-ref>`: external rot only blocks the PR if it's in a file the PR modified. Pre-existing rot elsewhere is reported under a "pre-existing broken link(s)" heading without failing the build, and is tracked by the weekly `link-rot` workflow, which keeps a single GitHub issue up to date. Internal-link failures block regardless of which files changed. Local runs omit the flag, so everything blocks.

**What it does not catch.** Staleness detection only works where a vendor returns an honest status code, so its reach is narrower than it looks:
- **Sigma-Aldrich and Cytiva never return one** — they reset the connection before any HTTP status. Between them that's ~40% of external links, and a discontinued part number there is undetectable at any frequency.
- **Soft-404s are invisible** — a vendor serving "product not found" with HTTP 200 reads as a healthy link.

Both still require manual review. `lychee` is pinned to 0.24.2 in both workflows because its JSON report is this script's input contract and has changed shape between releases before (#136); bump the pin and the local install together.

### Build error checking (myst strict build)

**Run this if you touched any link, image reference, directive, or table syntax.** `myst build --html` emits ⛔️-prefixed errors for broken links, missing images, and malformed directives but exits 0 regardless. `scripts/check-myst-build.py` wraps `myst build --html --strict` and fails only when an unfiltered ⛔️ error survives. This is what the `build-protocols` CI job gates on (`.github/workflows/protocols.yml`, issue #176).

```bash
python3 scripts/build-protocols.py            # generates process/module PDFs the Downloads cards link to
python3 scripts/build-materials-reference.py  # generates the guides/materials-reference.md include
python3 scripts/check-myst-build.py
```

Run the two generator scripts first — without them, `guides/materials-reference.md`'s `{include}` and every process page's Downloads `{button}` card report their gitignored `generated/` target as a genuinely missing file.

**Interpreting output.** ⛔️ (error) fails the build; ⚠️ (warning) is summarized but never fails it — this repo deliberately leaves warnings (legacy link syntax, duplicate identifiers, unrecognized frontmatter keys like `status`) non-blocking. Treat every ⛔️ as real **except** where `scripts/myst-build-false-positives.toml` documents a specific known false positive (currently: a figure in `membrane-pore-cx43/spec.md` sourced from a remote DevNote via `xref:`, which myst still checks for on local disk even though the file only exists remotely). Any new suppression belongs in that TOML file as an exact `file` + message `substring` match, not in `myst.yml`'s `error_rules:` — mystmd's `image-exists` rule (and potentially others) carries no per-file `key` in its warning payload, so `error_rules[].keys` file-scoping can never match it; a `myst.yml`-level suppression for such a rule would be repo-wide and would blind the check to a genuinely missing file anywhere else in the docs.
