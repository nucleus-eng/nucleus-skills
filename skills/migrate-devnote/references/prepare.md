# De-bloat, repair config, pin the CDK

## 3. De-bloat

Bundles and bulk downloads carry the same junk every time. Survey before
deleting, and keep everything uncommitted until the trim is done so git history
stays clean.

```bash
du -h -d 1 . | sort -rh
find . -type d \( -name _build -o -name __pycache__ -o -name .ipynb_checkpoints \
  -o -name node_modules -o -name .venv -o -name .git \) -prune -exec du -sh {} \;
find . -type f \( -iname '*.tar' -o -iname '*.tar.gz' -o -iname '*.zip' \) -exec du -sh {} \;
```

Standard removals: `_build/`, `__pycache__/`, `.ipynb_checkpoints/`,
`node_modules/`, `.venv/`, per-DevNote `.git/` directories, and archives sitting
beside their own already-extracted contents.

**Vendored CDK copies.** Older DevNotes shipped a local `src/cdk/` tree and
`platereader.py` next to the notebooks, with cells doing
`import platereader as pr`. Delete the vendored copies and repoint the import at
the packaged CDK. `module-Clpxp-Cells` had two 52 KB copies plus committed
`.pyc` files.

**Verify before deleting.** Not every archive is a duplicate — `onepot-sy`'s
`plasmids/PURE_plasmids.tar.gz` was genuine content. Check with `tar -tzf`
first.

**Never delete a notebook without asking.** Flag orphans instead.

**Large files.** GitHub hard-blocks any file over 100 MB at push time. Check
sizes before staging; use Git LFS or external storage. `Base_Cell`'s liposome
imaging CSVs (1.6 GB and 702 MB) cannot be committed as plain blobs.

## 4. Repair `curvenote.yml`

**A missing path is not automatically a dead reference.** It may be a path a
notebook *creates* at runtime. Grep the notebooks before pruning either the file
or the config key naming it.

This cost real time in PR #20: `thumbnail: "assets/thumbnail.png"` pointed at a
directory MECA had not shipped. Deleting the key as "dangling" broke the
notebook — `plt.savefig("../assets/thumbnail.png")` crashed on the missing
directory — *and* would have silently cost the DevNote its thumbnail. The fix
was `mkdir assets` and keep the key.

```bash
# every savefig target should write into a directory that exists
python3 - <<'PY'
import json, glob, os, re
for f in glob.glob('devnotes/*/**/*.ipynb', recursive=True):
    if '.ipynb_checkpoints' in f or '_build' in f: continue
    for c in json.load(open(f)).get('cells', []):
        if c.get('cell_type') != 'code': continue
        for m in re.finditer(r"savefig\(\s*[\"']([^\"']+)[\"']", "".join(c['source'])):
            p = m.group(1)
            d = os.path.normpath(os.path.join(os.path.dirname(f), os.path.dirname(p)))
            if os.path.dirname(p) and not os.path.isdir(d):
                print(f"{f} writes {p} -> missing {d}")
PY
```

**`resources:` globs.** Curvenote only uploads files matching a `resources:`
glob. A file-not-found at build time is usually a wrong glob, **not** a wrong
path in `main.md`. Check the globs before rewriting any content path —
`03_mthfs` lost a data file to `experimental/**/*` vs `experiments/**/*`. Also
trim globs pointing at directories that no longer exist after de-bloating.

**Downloads.** Confirm every `downloads:` entry resolves. `module-Clpxp-Cells`
referenced `general/clpxp-module-plasmids-01.zip`; the real file was
`general/Plasmids.zip`.

**Compute config.** Use `jupyter: true` — 15 of the migrated DevNotes do. Some
recovered bundles carry a stale `thebe: binder:` block pointing at the old
`bnext-bio/nucleus-developer-notes` repo. Replace it.

## 5. Pin the CDK

This is the most common live-compute failure, and the subject of issues #17
and #18.

Curvenote live compute runs **Python 3.14**. Every `toc` notebook needs a pinned
install cell as its first code cell:

```python
!pip install nucleus-cdk==0.5.0rc2 | tail -n2

# Surface a failed install here, rather than as a confusing ModuleNotFoundError
# in the import cell below.
import importlib.metadata as md
assert md.version("nucleus-cdk") == "0.5.0rc2", f"got {md.version('nucleus-cdk')}"
```

The assert matters because `| tail -n2` hides a failed install. Without it, the
real error surfaces much later as a baffling `ModuleNotFoundError`.

### Choosing the version

| Notebook imports | Pin | Notes |
|---|---|---|
| `from cdk.analysis.cytosol import platereader as pr` | `0.5.0rc2` | the older API; what nearly every migrated DevNote uses |
| `from cdk.instruments.platereader import ...` | `0.6.0rc2` | the new API; needs `--no-deps` |

**0.6.x deleted `cdk/analysis/cytosol/platereader.py`** — it moved to
`cdk/instruments/platereader/legacy/`. Pinning an old-API notebook to 0.6.x
breaks it outright. Check the imports before choosing.

Unpinned `pip install nucleus-cdk` resolves to whatever is newest (0.5.3 as of
2026-08-05). That drifts on every read and may not match the API the notebook
was written against.

`--no-deps` is needed **only for 0.6.x**, which declares `pyarrow>=18,<19`;
pyarrow publishes no cp314 wheels, so a plain install fails on Python 3.14.
Verified: `0.5.0rc2` installs cleanly on 3.14 with all 14 dependencies, so do
**not** add `--no-deps` there. `environment.yml` does not list several of its
dependencies — scikit-learn, openpyxl, jinja2, ordered-set, jupyter-bokeh — and
skipping them breaks the import.
