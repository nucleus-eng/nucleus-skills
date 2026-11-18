---
name: copyedit-pdf
description: Make a copy edit PDF of a MyST Markdown page. Use when someone wants to proofread, mark up or print a docs page, module spec or process page, and the edits must map back to lines in the `.md` source. Produces a double spaced PDF with the source line number beside every block, with MyST directives (tables, admonitions, figures, tabs, cards, Mermaid) rendered instead of shown raw. It does not build the docs site and does not edit the page.
---

# Copy edit PDF

A reviewer marks up a PDF. The author then has to find each mark in the
Markdown. This skill puts the source line number beside every block, so the
mark "line 94" points at line 94 of the `.md` file.

The PDF is a read-only render. Make the edits in the Markdown, never in the PDF.

## Run it

```bash
plugins/nucleus/skills/copyedit-pdf/scripts/copyedit-pdf.sh <page.md> <out.pdf> ["Title"]
```

The title defaults to the `title:` in the front matter. The page header shows
the path of the source file from the git root.

First run installs the pinned `myst-parser` into
`~/.cache/nucleus-copyedit-pdf`. Set `COPYEDIT_PDF_HOME` to use another
directory. Later runs reuse it.

Needs `node`, `npm` and `typst`. Needs `mmdc` (Mermaid CLI) only when the page
has a Mermaid diagram.

Run it once per page. For a set of pages, call it in a loop and name each PDF
after its page.

## What the PDF shows

The gutter number is a line in the `.md` file. The rules:

| Block | Number shown |
| --- | --- |
| Heading, list item, paragraph | The first line. A paragraph that spans lines shows a range, `121–122`. |
| Table | The caption's line on the caption. Each row carries its own line in a left column inside the table. |
| Admonition | The line of the opening fence on the title. Each paragraph inside carries its own line. |
| Figure | The opening fence on the image, the caption's own line on the caption. |
| Tab, card | The opening fence on the label or title. A card's link and footer carry their option lines. |
| Mermaid diagram | The range of the diagram source, not the fence lines. |
| Front matter | Title, subtitle and status only. Lines 2 to 4 in most pages. |

Blank lines, fences, `:label:` and `:class:` option lines, and HTML comments do
not appear. A number never refers to a line that is not in the source.

Text stays as written. Straight quotes stay straight. The renderer does not
fix, reflow or reword anything.

## What it renders

| Source | Result |
| --- | --- |
| `:::{table}` and plain pipe tables | A bordered table with a caption and a header row. |
| `:::{attention}`, `:::{hint}` and other admonitions | A tinted box with its kind and title. |
| `:::{figure}` | The local image and its caption. |
| `tab-set` and `tab-item` | One labelled section per tab. |
| `grid` and `card` | A box per card with title, link and footer. |
| ` ```mermaid ` | The diagram, rendered with `mmdc`. |
| `- [ ]` task lists | Checkboxes, nested as in the source. |

## Known limits

- **Remote images** are not fetched. A card image shows as a gray
  `[remote image omitted]` line that keeps its source line number.
- **A directive the script does not know** prints a `WARN unhandled directive`
  line on stderr, and its body renders as ordinary Markdown. Read the PDF for
  that block before you trust it, and add the directive to `scripts/render.mjs`.
- **Front matter** keys other than `title`, `subtitle` and `status` are
  omitted.
- **Link targets** are not printed. A link shows its text in blue.
- **Math, footnotes and cross references** are not handled. Nothing in the
  Nucleus pages uses them yet. The script warns on an unhandled node type.

## Check the output

Open the PDF and compare three line numbers against the source: one heading,
one table row and one list item. Each must name that exact line in the `.md`
file. The last number in the PDF is the last content line. Closing `:::` fences
carry no number, so it can sit a few lines before the end of the file. A
mismatch anywhere else means the renderer lost the position of a block. Report
it, and do not hand the PDF to a reviewer.

## Boundaries

- To build or publish the docs site, use the MyST build in `lint-docs`.
- To produce lab-ready protocol PDFs and BOM tables, use `build-boms`.
- To write or fix page content, use `author-myst-content`.

This skill ships a script because more than one Nucleus repo has MyST pages
that need review, and the format it reads is MyST, which no one repo owns.
