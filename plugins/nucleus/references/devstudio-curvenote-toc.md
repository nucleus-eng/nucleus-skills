# The `curvenote.yml` toc comment

A notebook-discovery contract between two stages, and nothing to do with the
figure-provenance record in
[`devstudio-figure-provenance.md`](devstudio-figure-provenance.md) — the two
were bundled together once, on the grounds that both are handoff formats. They
are, but they share no fields and no producer, and bundling them meant neither
had a clear owner.

`devstudio-devnote-g-to-devnote-m` writes these comments. `devstudio-assemble-devnote-assets`
reads them. `devstudio-pipeline.md` says where those stages sit; the format is
here.

## The problem it solves

`devstudio-devnote-g-to-devnote-m` knows which notebooks a DevNote needs before
any of them have been downloaded. It cannot list them as live toc entries — a
`toc:` pointing at a file that does not exist breaks the build — but it must not
lose the Drive URL either, or the assembly stage has nothing to fetch.

So the entry is written commented out, carrying its source URL in a trailing
comment:

```yaml
toc:
  - file: main.md
  # - file: experiments/YYYYMMDD-slug/Analysis.ipynb  # https://colab.research.google.com/drive/<ID>
  # - file: experiments/YYYYMMDD-slug/notebook.ipynb  # https://drive.google.com/file/d/<ID>/view
```

Both Colab and Drive URL forms appear; the notebook may live as either. The Drive ID
is extracted from whichever form is present:

| URL form | Drive ID is |
| --- | --- |
| `https://colab.research.google.com/drive/<ID>` | the segment after `/drive/` |
| `https://drive.google.com/file/d/<ID>/view` | the segment between `/d/` and `/view` |

Extraction lives here rather than with the consumer because it is derived from the URL
shapes above — a third form would otherwise mean two edits, and the second would be
the one nobody remembered.

`devstudio-assemble-devnote-assets` downloads each notebook to the path the
entry names, then uncomments that entry — and only that entry:

```yaml
  - file: experiments/YYYYMMDD-slug/Analysis.ipynb
```

## Why uncommenting is per-file, not a final sweep

A commented entry whose download failed must stay commented. Uncommenting
everything once assembly finishes would put a missing notebook into the toc and
break the venue build, with the failure surfacing at publish time rather than at
assembly time — far from the stage that caused it.

The commented entry is therefore also the record of what is still outstanding: a
DevNote with commented toc lines left in it has assets that never arrived, and
that is readable without re-running anything.
