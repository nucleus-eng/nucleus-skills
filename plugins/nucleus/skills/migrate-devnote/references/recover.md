# Enumerate and recover

## 1. Enumerate what is published

The venue site serves machine-readable JSON. No scraping or login needed.

**Fetch every collection page.** Missing one silently hides whole groups of
DevNotes. An earlier attempt fetched three pages and reported 26 published; the
real figure is 49. `index.json` alone is not enough either — it lists only the
most recent DevNotes.

```bash
for c in index collections-core collections-contrib collections-ai-scientist \
         collections-workshops-and-courses collections-devcell-node-chicago \
         collections-devcell-node-london; do
  curl -s -A "Mozilla/5.0" "https://devnotes.nucleus.engineering/$c.json" -o "c-$c.json"
done

python3 - <<'PY'
import json, glob
pub = {}
def walk(n):
    if isinstance(n, dict):
        if isinstance(n.get('key'), str) and 'slug' in n:
            pub[n['key']] = (n['slug'], n.get('title'))
        for v in n.values(): walk(v)
    elif isinstance(n, list):
        for v in n: walk(v)
for f in glob.glob('c-*.json'): walk(json.load(open(f)))
for k, (s, t) in sorted(pub.items(), key=lambda kv: kv[1][1] or ''):
    print(f"{str(t)[:54]:56} {s:36} {k}")
PY
```

`key` is the **work key**. It must match `project.id` in the DevNote's
`curvenote.yml`, or a submission creates a new work instead of updating the
existing one. `slug` is only the site URL, and the two often differ:
`bnext-devnotes-clpxp-pure-cells-01` is a slug; its key is
`nucleus-devnote-core-clpxp_module_cells-01`. **Match on key, never on slug.**

Diff that against the repo. Parse the YAML properly — several `curvenote.yml`
files have `id:` keys nested under `exports:` and `authors:` that a plain grep
matches first:

```bash
python3 - <<'PY'
import glob, os, yaml
for y in sorted(glob.glob('devnotes/*/curvenote.yml')):
    pid = ((yaml.safe_load(open(y)) or {}).get('project') or {}).get('id')
    print(f"{pid or '*** NO project.id ***':52} {os.path.basename(os.path.dirname(y))}")
PY
```

Sanity-check that the per-collection counts add up to the total. An incomplete
fetch gives a confidently wrong answer, and nothing about the output looks
suspicious.

Write the result into `devnote-migration-status.md`. Never treat that file as
the work list — it has been out of date before.

## 2. Recover the source (MECA archive)

Every published article links a MECA computational archive with the full source
bundle: `curvenote.yml`, `main.md`, `environment.yml`, all `toc` notebooks, and
the data files.

The download URL carries a content hash, so it cannot be guessed. Read it off
the article page:

```bash
SLUG=Bhasin-20260421
curl -s -A "Mozilla/5.0" "https://devnotes.nucleus.engineering/articles/$SLUG" \
  | grep -oE 'https://pub\.curvenote\.com/[^"]+\.zip' | sort -u
```

A plain `curl` without a browser `User-Agent` gets a **403**.

Some articles list more than one zip. Three cases, and they are different things:

| Zip name | What it is |
|---|---|
| `curvenote-<hash>.zip` | the MECA archive |
| `curvenote_0`, `curvenote_1` | duplicate MECA archives. Verified on two articles: they differ **only** in `manifest.xml`. Use either. |
| any other name, e.g. `GenBank files-<hash>.zip` | a `downloads:` asset, **not** an archive. Useful if the archive dropped that file. |

Unzip and work from `bundle/`:

```bash
unzip -q archive.zip -d recovered && ls recovered/bundle
```

`bundle/` holds the source. `files/` holds content-addressed *render* output —
figure PNGs and notebook text outputs under hashed names. Do not mistake
`files/` for recovered source; only one of `03_mthfs`'s 15 `files/` entries was
also a repo file.

### What the archive contains, and what it silently omits

The archive ships the `toc` files, `curvenote.yml`, `environment.yml`, the
modules a `toc` notebook imports, and everything matched by the `resources:`
globs **as they were at the build**. Nothing else.

**Anton Molina's rule, stated exactly: content that is neither in the `toc` nor
matched by a working `resources:` glob is not in the archive.** It is not that
the DevNote never had that content. Check before you conclude anything.

**A broken glob strips content silently, and the archive looks fine.** Verified
on `03_mthfs`: its published archive carries the pre-fix typo
`experimental/**/*`, and is missing all six raw data files, both platemaps, four
generated PNGs, and the `MTHFS-labnotebook.pdf` named in `downloads:`. A DevNote
recovered from that archive cannot re-execute its notebook — the input data is
gone — and its download link resolves to nothing.

**So read `bundle/curvenote.yml` before you trust the bundle.** It records the
config the build actually used, which can be older than both the repo and the
live page. Then audit the bundle against that config:

```bash
python3 - recovered/bundle <<'PY'
import sys, os, glob as g, yaml
b = sys.argv[1]
p = (yaml.safe_load(open(os.path.join(b, 'curvenote.yml'))) or {}).get('project') or {}
for r in (p.get('resources') or []):
    n = sum(1 for h in g.glob(os.path.join(b, r), recursive=True) if os.path.isfile(h))
    print(f"resource {r:28} -> {n} files" + ("   *** MATCHES NOTHING ***" if not n else ""))
for d in (p.get('downloads') or []):
    f = d.get('file')
    if f: print(f"download {f}  {'OK' if os.path.isfile(os.path.join(b, f)) else '*** MISSING ***'}")
for t in (p.get('toc') or []):
    f = t.get('file')
    if f: print(f"toc      {f}  {'OK' if os.path.isfile(os.path.join(b, f)) else '*** MISSING ***'}")
PY
```

A glob that matches nothing is either dead config to trim, or the reason content
is missing. Tell the two apart by checking what `main.md` references.

**`extends: base.yml` hides real config.** MECA drops `base.yml`, so
`resources:`, `license:` and `exports:` can all read as empty when the project
inherited them. Do not conclude the DevNote had none. All four Core-batch
archives extend `base.yml`; two of them report no license and no exports.

**A notebook in the bundle is not necessarily article content.** All four of
`019ed70b`'s `analysis.ipynb` files ship as resources, but its `toc` lists only
`main.md`, and `main.md` embeds the pre-generated PNGs as static figures. That
is the author's design, not a bug. Adding a notebook to the `toc` changes what
the article publishes — ask first.

## 3. Recover when there is no MECA archive

Not every published article has one. Both IGOR rounds
(`bnext-devnotes-igor-260324`, `bnext-devnotes-igor-260422`) offer no zip at
all. The source is still recoverable, because the venue publishes every asset
individually under `pub.curvenote.com/<siteId>/public/`.

Two things make it work:

1. **`config.json`** at `pub.curvenote.com/<siteId>/config.json` carries the
   project frontmatter — `id` (the work key), title, authors, affiliations,
   date, `banner`, `thumbnail` and `toc`. It has no `license`, so licensing
   still needs a human.
2. **`main.md`** carries the original relative paths. You need it, because the
   published filenames are lossy: the site truncates each stem to **20
   characters** and appends a content hash.
   `figures/viz-01-test-split-sigmoid_rate-1-h.png` is published as
   `viz-01-test-split-si-<hash>.png`.

`scripts/recover-no-meca.py` does this. It reports the work key, the `toc`,
every file it resolved, and anything it could not:

```bash
python3 .claude/skills/migrate-devnote/scripts/recover-no-meca.py \
  bnext-devnotes-igor-260324 recovered/
```

The mechanism, if you need to do it by hand: fetch the article page, collect the
asset URLs, read `config.json`, fetch `main.md`, extract every path it
references, and match each one to an asset by `stem[:20]`. A `banner` or
`thumbnail` from `config.json` already carries its hash, so match those
literally.

**Ignore anything the author commented out.** Strip `<!-- ... -->` before
collecting references, or a disabled figure looks like missing content. IGOR
Round 2 has exactly one of these.

Then treat whatever stays unresolved as a real gap and report it. Round 2
references `./workspace/workspace_data.csv`, which was never published; that
link is broken on the live site too.

### What this path cannot recover

Only what the venue published. Files an article `{include}`s but that were never
uploaded stay missing, and so do plugins providing custom roles. Both IGOR
rounds `{include} discourse.md` and `{include} ges.md` and use `{claim}` and
`{evidence}` roles; none of it was ever published, and the live pages render the
literal string `discourse.md`. Report it and ask the author. Do not invent the
files.

If another DevNote in the repo looks like it holds a missing file, **verify
before copying.** `fwm-aria-d1` embeds two sub-articles that look like the two
IGOR rounds. `iter2` really is Round 2 — identical body, 11 byte-identical
figures. `iter1` is a different report, with a different abstract and five
different figures. Copying from it would have injected the wrong content. And
even a verified match is a content addition to a published article, so ask.

### Repo-level files MECA never ships

The archive is a *build product*, so it omits generated and repo-level files.
Expect to restore:

| Missing | Fix |
|---|---|
| `banner.webp` / `banner-2.webp` | copy from a sibling — byte-identical across all DevNotes |
| `lorem.mjs` | same |
| `LICENSE.md`, `README.md`, `.gitignore` | same |
| `base.yml` (if `extends: base.yml`) | delete the `extends:` line and inline what it supplied. Do **not** copy a sibling's `base.yml` — the repo holds five copies that disagree. Model the rebuilt file on `devnotes/2026-garenne-pH-sensor/curvenote.yml`. |
| notebook-generated files (thumbnails, PNGs) | **do not delete the config that references them** — see `prepare.md` |

### Check for drift

The archive reflects the last *submitted* build, which can lag the live page.
Before submitting, diff the recovered `main.md` against the live article so you
do not silently revert a later edit.

Normalize both sides first — lowercase, strip punctuation and smart quotes — or
MyST syntax like `{ref}` roles, `:::{figure}` directives and LaTeX produces a
flood of false differences.
