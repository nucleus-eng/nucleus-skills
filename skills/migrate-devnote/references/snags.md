# Snag catalogue

Symptom → cause → fix. Most failures in this pipeline have been seen before.
Check here before diagnosing from scratch.

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'cdk'` in live compute | no install cell, or the install failed silently | pinned install cell plus version assert — `prepare.md` §5 |
| Install cell fails on Python 3.14 | 0.6.x pulls `pyarrow`, which has no cp314 wheels | add `--no-deps`, or pin 0.5.0rc2 |
| `ImportError` on `cdk.analysis.cytosol` | pinned to 0.6.x, which moved the module | pin 0.5.0rc2 |
| Published DevNote still shows old errors after a fix | `submit` does not re-execute notebooks | re-run and commit outputs — `verify-submit.md` §6 |
| Notebooks pass but no figures render | `MPLBACKEND` forced to `Agg` | never set it; diff PNG counts |
| A figure renders blank | a CDK helper calls `plt.show()`, closing it before `savefig` | embed from the notebook cell instead |
| `devnote.pdf` export fails | space in a Typst label, or a wrong-case `{ref}` | rename the label, fix the reference — `verify-submit.md` §7 |
| Typst: `label <x> does not exist in the document` | a container Typst cannot convert (`{grid}`) was dropped, taking its labelled children with it. Look for an earlier `Unhandled Typst conversion for node of ...` | removing the wrapper fixes it, but that is a layout change — ask the author |
| `Unhandled Typst conversion for node of ...` but the PDF still builds | the node had no labelled children, so nothing dangles | benign; do not chase it |
| File-not-found at build, path looks correct | `resources:` glob does not match | fix the glob, not the path — `prepare.md` §4 |
| Notebook crashes writing a file | a needed directory was pruned as "missing" | recreate it; check `savefig` targets |
| `Could not find static resource` in downloads | renamed or absent download target | point at the real filename |
| `No authors provided an email` | author has no `email` in `curvenote.yml` | needs a real contact — **do not invent one** |
| Submit reports "Created a new work" | work resolution is scoped to the submitting account | expected locally; let CI submit |
| 403 fetching an article page | no browser `User-Agent` | pass `-A "Mozilla/5.0"` |
| Enumeration finds too few DevNotes | not every collection page was fetched | fetch all of them; check counts sum |
| Recovered DevNote has no input data, so a notebook cannot re-run | the archive was built with a broken `resources:` glob, so the data was never in it | read `bundle/curvenote.yml`, audit every glob — `recover.md` §2 |
| Recovered DevNote reports no license, no exports, no resources | `extends: base.yml`, and MECA drops `base.yml` | inline what base supplied; do not assume it had none |
| A `downloads:` target is absent from the bundle | same broken-glob cause | check the article page — download assets are published as their own zips |
| Preview renders unstyled, cells are dead, "Launch Jupyter" gives 494 | accumulated preview-token cookies — see "Reviewing is client-side" below | clear cookies for `devnotes.nucleus.engineering` |

## Reviewing is client-side, and it degrades over a long session

Reviewing a batch of submission previews eventually breaks the venue site. The
symptom set is distinctive: the article MAY render **unstyled** — Times New Roman,
blue underlined links, visible `¶` anchors — embedded Jupyter cells do not respond to
clicks at all, and "Launch Jupyter" lands on a Vercel error page reading
**494 `REQUEST_HEADER_TOO_LARGE`**.

Nothing is wrong with the build. `devnotes.nucleus.engineering` sits behind
Vercel, which rejects any request whose headers exceed roughly **32KB** before
the app runs. Preview tokens are the thing that grows. The site sets one
`__cn_preview-<submissionId>` cookie per preview — about **515 bytes** each,
wrapping a JWT with `scope: submission` and a five-day life — so the link
survives the `?preview=` param being dropped. The name is keyed per submission,
so they **accumulate rather than overwrite**, and they are not expired with
their contents: a measured jar held a cookie created 14 days earlier whose token
had been dead for over a week.

Measured on 2026-08-05, mid-review: **70 cookies, 35,956 bytes.** Nothing else
is stored on that host, so every byte of it is preview tokens.

The load order is why it looks like a build fault:

| Request | Cookies sent? | Result |
|---|---|---|
| the preview document, arrived at from Curvenote | no — `Sec-Fetch-Site: cross-site`, so `SameSite` withholds them | **200**, HTML renders |
| its CSS and JS | yes — same-site | **494**, so no styling and no JavaScript |
| clicking a cell | — | nothing; the script never loaded |
| "Launch Jupyter" | yes — same-site navigation | **494** error page |

That first row is a trap. Copying request headers off the document request shows
no `Cookie:` header and a ~800-byte total, which looks exonerating. **Inspect a
same-site sub-resource instead.**

Confirm from the shell in ten seconds, against any public build URL:

```bash
U=https://scms.curvenote.com/build/<build-id>
curl -s -o /dev/null -A "Mozilla/5.0" -w "clean: %{http_code}\n" "$U"
BIG=$(python3 -c "print('a='+'x'*48000)")
curl -s -o /dev/null -A "Mozilla/5.0" -H "Cookie: $BIG" -w "bloated: %{http_code}\n" "$U"
```

`clean: 200` with `bloated: 494` proves the server is healthy and the browser is
at fault. `curl -D -` also prints `x-vercel-id: sfo1::...`, whose region prefix
appears in the error the browser shows.

To measure the jar itself, read Firefox's cookie store rather than the Storage
panel, which offers neither a size column nor a JSON export. This prints names
and byte counts only, never values:

```bash
P=~/Library/Application\ Support/Firefox/Profiles/<profile>
T=$(mktemp -d); cp "$P"/cookies.sqlite* "$T"/    # Firefox locks the live file
sqlite3 -column -header "$T/cookies.sqlite" "
  select host, count(*) n, sum(length(name)+length(value)+2) bytes
  from moz_cookies group by host order by bytes desc limit 12;"
rm -rf "$T"
```

Fix: clear cookies for **`devnotes.nucleus.engineering`**. Review from a
dedicated browser profile rather than a private window — private windows also
work, but they disable extensions and drop your login too, which confuses the
diagnosis and is painful across a batch.

The bug is Curvenote's, not ours. `devnotes.nucleus.engineering` is a custom
domain pointed at their venue app; the cookie prefix (`__cn_`), the token issuer
(`scms.curvenote.com`) and the Vercel headers are all theirs. Reported upstream
as **curvenote/curvenote#1045**. Expect it to recur every batch until that is
fixed — roughly one preview per 515 bytes, so about 60 previews to the wall.

Diagnosed 2026-08-06, after the four Core submissions were wrongly suspected of
having lost their compute config. They had not: the draft and submit CI runs
were the same workflow, same CLI image, both loading `environment.yml` for all
four DevNotes, with no compute error in either log. **Check the client before
suspecting the build.**

## What to automate, and what not to

**Safe to automate:** enumeration, MECA download and unzip, de-bloat sweeps,
install-cell rewriting, notebook execution, output and figure-count
verification, `curvenote check`, draft submission, and gap reporting against the
tracker.

**Keep human:**

- **The licensing and curation decision.** Never automate it.
- Content review — a human reading `main.md` end to end.
- Deleting any notebook.
- Inventing missing author contact details.
- Any edit to collaborator prose.

A reasonable build order for issue #21 is one script per stage, with a
machine-readable report between stages. That makes a failure attributable, and
gives the curation gate a natural place to sit: after enumeration, before
recovery.

If a stage bounds its own coverage — a top-N cap, a sampling step, a skipped
retry — log what it dropped. Silent truncation reads as "covered everything"
when it did not. That is the same class of error that had the tracker reporting
26 published DevNotes when there were 49.
