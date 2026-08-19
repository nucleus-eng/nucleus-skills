# Execute, validate, submit

## 6. Execute the notebooks

`curvenote submit` renders saved outputs, so **every notebook must be
re-executed and its outputs committed** after any code change.

```bash
python -m venv venv && ./venv/bin/pip install "nucleus-cdk==0.5.0rc2" nbclient ipykernel
```

**Never set `MPLBACKEND`.** ipykernel defaults to the `matplotlib_inline`
backend, and that backend is what captures figures as saved outputs. Forcing
`Agg` makes every notebook pass while saving **zero** figures — a green run that
publishes figure-less DevNotes. This nearly shipped in PR #20.

Always diff image-output counts against the pristine bundle afterwards:

```bash
python3 - <<'PY'
import json, sys
def pngs(f):
    nb = json.load(open(f))
    return sum(1 for c in nb['cells'] for o in c.get('outputs', [])
               if 'image/png' in (o.get('data') or {}))
for f in sys.argv[1:]: print(pngs(f), f)
PY
```

Also confirm no saved `output_type == "error"` remains, and spot-check that
generated PNGs are not blank. Several CDK plot helpers call `plt.show()`
internally, which closes the figure in the inline backend — a later
`plt.savefig()` then writes an *empty* image. That silently blanked
`onepot-sy`'s Figure 4.

Where possible, embed figures directly from notebook cells (`#fig:label`) rather
than saving PNGs separately. That sidesteps the failure mode entirely.

**Do not run `git checkout -- devnotes/` to clean up after a debugging run.**
That is exactly what discarded freshly-passing outputs in PR #13 and left stale
tracebacks baked into the committed files.

## 7. Validate

```bash
cd devnotes/<devnote>
npx --yes curvenote@latest check bnext-devnotes --kind devnote
```

**Typst labels cannot contain spaces.** A `:name:` or `:label:` with a space
fails the PDF export with `label <...> does not exist in the document`. Watch
for case mismatches between a label and its `{ref}` too: `fig:ClpX S` defined
against a `fig:ClpX s` reference broke `module-Clpxp-Cells`, and PR #9 fixed six
more of these. `main.md` files mix `:name:` and `:label:`, so grep for both.

```bash
grep -nE "^:(name|label):.*[A-Za-z0-9] +[A-Za-z0-9]" main.md   # labels with spaces
```

Known-benign messages: `Unhandled JATS conversion for node of "tabSet"` for any
DevNote using tab-sets, and `Image is too large ... to convert to webp`. When
unsure whether a message is pre-existing, run the same check against a DevNote
already merged to `main` and compare.

## 8. Submit

**Draft submits are cheap.** They do not reach the editor panel and do not
create venue submissions. Iterate on drafts freely.

```bash
cd devnotes/<devnote>
npx --yes curvenote@latest submit bnext-devnotes --kind devnote \
  --collection developer-cells --draft -y
```

**"Created a new work" from a local submit is expected, not a bug.** Work
resolution is scoped to the submitting account, so a personal token cannot see
or update a work owned by someone else. Confirmed by draft-submitting two
DevNotes already on `main` (`module-Clpxp-Cytosol`, `lipid-prep`) — both report
it. The key format is irrelevant.

To check which work a submit actually hit, read
`_build/logs/curvenote.submit.json`. An existing work shows its original
`work.date_created`; a duplicate shows today's date.

**The real publish path is CI.** `submit.yml` runs on push to `main` with the
venue-level `secrets.CURVENOTE_TOKEN`, which resolves works correctly.
`draft.yml` runs on PRs and posts preview links plus check results as a PR
comment — that comment is the best pre-merge signal. Use local drafts for
build and QA, and let the merge do the real submission.

Clean up afterwards: `curvenote submit` drops an untracked PDF export into each
DevNote directory per its `exports:` config. Remove them before committing.

## 9. Update the tracker

`devnote-migration-status.md` at the repo root is the record. Per DevNote,
update its status and keep the summary counts honest by regenerating them, not
by editing them by hand.

"Content reviewed" means a human read `main.md` from start to end. It cannot be
automated, and neither can the licensing gate.
