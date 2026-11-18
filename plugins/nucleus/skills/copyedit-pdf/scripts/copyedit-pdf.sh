#!/usr/bin/env bash
# Render one MyST Markdown file to a double-spaced PDF whose line numbers
# match the source file. Usage: copyedit-pdf.sh <file.md> <out.pdf> [title]
#
# Needs: node, npm, typst. Needs mmdc only when the page has a Mermaid diagram.
# First run installs myst-parser into $COPYEDIT_PDF_HOME (default
# ~/.cache/nucleus-copyedit-pdf). Later runs reuse it.
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <file.md> <out.pdf> [title]" >&2
  exit 2
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
out="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"

for tool in node npm typst; do
  command -v "$tool" >/dev/null || { echo "missing tool: $tool" >&2; exit 1; }
done
[ -f "$src" ] || { echo "no such file: $1" >&2; exit 1; }

home="${COPYEDIT_PDF_HOME:-$HOME/.cache/nucleus-copyedit-pdf}"
mkdir -p "$home"
cp "$here/render.mjs" "$here/package.json" "$home/"
if [ ! -d "$home/node_modules/myst-parser" ]; then
  (cd "$home" && npm install --silent --no-audit --no-fund)
fi

# Title: the argument, else the front matter title, else the file name.
title="${3:-}"
if [ -z "$title" ]; then
  title="$(sed -n '2,/^---$/ s/^title: *"\{0,1\}\(.*[^"]\)"\{0,1\} *$/\1/p' "$src" | head -1)"
fi
[ -n "$title" ] || title="$(basename "$src")"

# Path shown in the header: relative to the git root when there is one.
rel="$(basename "$src")"
if root="$(git -C "$(dirname "$src")" rev-parse --show-toplevel 2>/dev/null)"; then
  rel="${src#"$root"/}"
fi

work="$(mktemp -d)"
trap 'rm -rf "${work:?}"' EXIT

(cd "$home" && REL_PATH="$rel" node render.mjs "$src" "$work/page.typ" "$work" "$title")
typst compile --root / "$work/page.typ" "$out"
echo "wrote $out"
