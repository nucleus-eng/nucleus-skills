// Render one MyST Markdown file to Typst, with the source line number of every block.
// usage: node render.mjs <file.md> <out.typ> <workdir> [displayName]
// env:   REL_PATH  path shown in the page header (defaults to the <file.md> argument)
// Needs `myst-parser` resolvable from this file's directory. copyedit-pdf.sh sets that up.
import { mystParse } from 'myst-parser';
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';

const [srcPath, outPath, workDir, displayName] = process.argv.slice(2);
const srcText = fs.readFileSync(srcPath, 'utf8');
const SRC = srcText.split('\n');
const srcDir = path.dirname(path.resolve(srcPath));
const rel = process.env.REL_PATH || srcPath;

// ---------- typst helpers ----------
const q = (s) => '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, ' ') + '"';
const T = (s) => `#t(${q(s)});`;

function inline(nodes, base) {
  return (nodes || []).map((n) => inl(n, base)).join('');
}
function inl(n, base) {
  switch (n.type) {
    case 'text': return T(n.value);
    case 'strong': return `#strong[${inline(n.children, base)}];`;
    case 'emphasis': return `#emph[${inline(n.children, base)}];`;
    case 'inlineCode': return `#raw(${q(n.value)});`;
    case 'link': return `#link(${q(n.url)})[#text(fill: rgb("#1a56b0"))[${inline(n.children, base)}]];`;
    case 'break': return '#linebreak();';
    case 'cite': return T('@' + (n.label || (n.children && n.children[0] && n.children[0].value) || ''));
    case 'html': return '';
    case 'image': return `#text(fill: gray)[${T('[image: ' + (n.alt || n.url) + ']')}];`;
    default:
      if (n.children) return inline(n.children, base);
      if (n.value) return T(n.value);
      return '';
  }
}

// ---------- row collection ----------
const rows = [];
const lnLabel = (a, b) => (b && b !== a ? `${a}–${b}` : `${a}`);
function emit(ln, body, ctx, extra = {}) {
  rows.push({ ln, body, indent: ctx.indent, decor: ctx.decor.slice(), ...extra });
}

const KIND_COLOR = { attention: '#c2410c', hint: '#0e7490', note: '#1d4ed8', warning: '#b91c1c', tip: '#15803d' };
let imgCount = 0;

function startLine(n, base) { return n.position ? n.position.start.line + base - 1 : null; }
function endLine(n, base) { return n.position ? n.position.end.line + base - 1 : null; }

function findLine(text, from) {
  for (let i = from; i <= SRC.length; i++) if (SRC[i - 1].trim() === text.trim()) return i;
  return null;
}
function findOptionLine(prefix, from, to) {
  for (let i = from; i <= to; i++) if (SRC[i - 1].trim().startsWith(prefix)) return i;
  return null;
}

function blockChildren(children, ctx, base) {
  for (const c of children || []) block(c, ctx, base);
}

function block(n, ctx, base, hint = {}) {
  switch (n.type) {
    case 'heading': {
      const ln = startLine(n, base);
      emit(lnLabel(ln), `#heading-${Math.min(n.depth, 4)}[${inline(n.children, base)}]`, ctx);
      return;
    }
    case 'paragraph': {
      const s = hint.line ?? startLine(n, base);
      const e = hint.line ? null : endLine(n, base);
      emit(lnLabel(s, e), `#body-par[${inline(n.children, base)}]`, ctx);
      return;
    }
    case 'list': return list(n, ctx, base);
    case 'code': return code(n, ctx, base);
    case 'html': return; // comments
    case 'thematicBreak': return;
    case 'mystDirective': return directive(n, ctx, base);
    case 'admonition': return admonition(n, ctx, base, hint);
    case 'container': return container(n, ctx, base, hint);
    case 'table': return table(n, ctx, base, hint);
    case 'image': {
      emit(hint.line ? `${hint.line}` : '', imageBody(n.url), ctx);
      return;
    }
    default:
      process.stderr.write(`WARN unhandled node ${n.type} at ${startLine(n, base)}\n`);
      if (n.children) blockChildren(n.children, ctx, base);
  }
}

function imageBody(url) {
  if (/^https?:/.test(url)) return `#text(fill: gray, size: 9pt)[#t("[remote image omitted: ${url.split('/').pop().slice(0, 40)}]");]`;
  const abs = path.resolve(srcDir, url);
  if (!fs.existsSync(abs)) return `#text(fill: gray)[#t("[image not found: ${url}]");]`;
  return `#align(center, image(${q(abs)}, width: 75%))`;
}

function list(n, ctx, base) {
  let i = n.start || 1;
  for (const item of n.children) {
    const first = item.children.find((c) => c.type === 'paragraph');
    const mark = item.checked === false ? '#box(width: 0.65em, height: 0.65em, stroke: 0.7pt + black, baseline: 0.05em);'
      : item.checked === true ? '#box(width: 0.65em, height: 0.65em, stroke: 0.7pt + black, baseline: 0.05em)[#align(center + horizon)[#text(size: 0.6em)[#t("✓");]]];'
      : n.ordered ? T(`${i}.`) : '#t("•");';
    const li = startLine(item, base);
    const fc = first ? inline(first.children, base) : '';
    emit(`${li}`, `#list-item(${ctx.indent}, [${mark}], [${fc}])`, ctx);
    const sub = { ...ctx, indent: ctx.indent + 1 };
    for (const c of item.children) {
      if (c === first) continue;
      block(c, sub, base);
    }
    i++;
  }
}

function code(n, ctx, base) {
  const s = startLine(n, base);
  // root-level yaml front matter is the first node at line 1
  if (s === 1 && base === 1) return frontmatter(n, ctx);
  const body = n.value;
  const nLines = body.split('\n').length;
  const first = s + 1; // fence line is s
  if (n.lang === 'mermaid') {
    const id = ++imgCount;
    const mmd = path.join(workDir, `diagram-${path.basename(outPath, '.typ')}-${id}.mmd`);
    const png = mmd.replace('.mmd', '.png');
    fs.writeFileSync(mmd, body);
    execFileSync('mmdc', ['-i', mmd, '-o', png, '-s', '3', '-b', 'white', '-q'], { stdio: 'inherit' });
    emit(lnLabel(first, first + nLines - 1), `#align(center, image(${q(png)}, width: 100%))`, ctx);
    return;
  }
  emit(lnLabel(first, first + nLines - 1), `#block(fill: luma(245), inset: 6pt, width: 100%, raw(${q(body)}, block: true))`, ctx);
}

function frontmatter(n, ctx) {
  const lines = n.value.split('\n');
  const keys = { title: 'doc-title', subtitle: 'doc-subtitle', status: 'doc-status' };
  lines.forEach((l, i) => {
    const m = l.match(/^(\w+):\s*"?(.*?)"?\s*$/);
    if (m && keys[m[1]]) {
      emit(`${i + 2}`, `#${keys[m[1]]}[${T(m[1] === 'status' ? 'Status: ' + m[2] : m[2])}]`, ctx);
    }
  });
}

function admonition(n, ctx, base, hint) {
  const kind = n.kind || 'note';
  const color = KIND_COLOR[kind] || '#444444';
  const title = n.children.find((c) => c.type === 'admonitionTitle');
  const dctx = { ...ctx, decor: [...ctx.decor, { type: 'adm', color, id: ++decorId }] };
  const label = kind[0].toUpperCase() + kind.slice(1);
  emit(hint.line ? `${hint.line}` : '', `#text(weight: "bold", fill: rgb(${q(color)}))[${T(label + ': ')}${title ? inline(title.children, base) : ''}]`, dctx);
  blockChildren(n.children.filter((c) => c !== title), dctx, base);
}
let decorId = 0;

function container(n, ctx, base, hint) {
  const S = hint.line ?? null;
  const cap = n.children.find((c) => c.type === 'caption');
  const rest = n.children.filter((c) => c !== cap);
  if (n.kind === 'table') {
    if (cap) {
      const capInl = inline(cap.children.flatMap((p) => p.children || []), base);
      emit(S ? `${S}` : '', `#table-caption[#strong[#t("Table: ");]${capInl}]`, ctx);
    }
    for (const c of rest) block(c, ctx, base);
    return;
  }
  if (n.kind === 'figure') {
    for (const c of rest) {
      if (c.type === 'image') emit(S ? `${S}` : '', imageBody(c.url), ctx);
      else block(c, ctx, base);
    }
    if (cap) {
      // caption paragraph carries real position
      const p = cap.children[0];
      const ps = p && p.position ? startLine(p, base) : null;
      emit(ps ? `${ps}` : '', `#fig-caption[#strong[#t("Figure: ");]${inline((p && p.children) || [], base)}]`, ctx);
    }
    return;
  }
  blockChildren(n.children, ctx, base);
}

function table(n, ctx, base) {
  const nCols = n.children[0].children.length;
  const head = n.children[0];
  const cell = (c) => `[${inline(c.children, base)}]`;
  const rowsOut = [];
  n.children.forEach((r, ri) => {
    const ln = startLine(r, base);
    rowsOut.push(`table.cell(align: right + top)[#text(font: MONO, size: 7pt, fill: gray)[${ln}]]`);
    r.children.forEach((c) => {
      rowsOut.push(ri === 0 ? `table.cell(fill: luma(235))[#strong${cell(c)}]` : cell(c));
    });
  });
  const cols = '(2.2em, ' + Array(nCols).fill('1fr').join(', ') + ')';
  const body = `#block(width: 100%)[#set text(size: 8.5pt); #set par(leading: 0.9em); #table(columns: ${cols}, inset: (x: 4pt, y: 6pt), stroke: 0.5pt + luma(150), table.header(table.cell(fill: luma(235))[], ${head.children.map((c) => `table.cell(fill: luma(235))[#strong${cell(c)}]`).join(', ')}), ${rowsOut.slice(nCols + 1).join(', ')})]`;
  emit('', body, ctx, { tableRows: true });
}

function directive(n, ctx, base) {
  const S = startLine(n, base);
  const E = endLine(n, base);
  // resolved directives: admonition / container
  if (n.children && n.children.length) {
    for (const c of n.children) block(c, ctx, base, { line: S });
    return;
  }
  const name = n.name;
  let value = n.value || '';
  const ownOptions = { ...(n.options || {}) };
  {
    const vl = value.split('\n');
    let k = 0;
    while (k < vl.length && /^:[\w-]+:/.test(vl[k])) {
      const m = vl[k].match(/^:([\w-]+):\s*(.*)$/);
      ownOptions[m[1]] = m[2];
      k++;
    }
    value = vl.slice(k).join('\n');
  }
  const vLines = value.split('\n');
  const lead = vLines.findIndex((l) => l.trim() !== '');
  let vBase = S + 1;
  if (lead >= 0) {
    const L = findLine(vLines[lead], S + 1);
    if (L) vBase = L - lead;
  }
  const sub = () => {
    const tree = mystParse(value, {});
    blockChildren(tree.children, ctx, vBase);
  };
  if (name === 'tab-set' || name === 'grid') { return sub(); }
  if (name === 'tab-item') {
    emit(`${S}`, `#tab-label[${T('Tab: ' + n.args)}]`, ctx);
    const inner = { ...ctx, indent: ctx.indent + 1 };
    const tree = mystParse(value, {});
    blockChildren(tree.children, inner, vBase);
    return;
  }
  if (name === 'card') {
    const dctx = { ...ctx, decor: [...ctx.decor, { type: 'card', color: '#555555', id: ++decorId }] };
    emit(`${S}`, `#strong[${T(n.args)}]`, dctx);
    const opts = ownOptions;
    if (opts.link) emit(`${findOptionLine(':link:', S + 1, E) || ''}`, `#text(size: 8pt, font: MONO, fill: gray)[${T('Link: ' + opts.link)}]`, dctx);
    if (opts.footer) emit(`${findOptionLine(':footer:', S + 1, E) || ''}`, `#text(size: 9pt, style: "italic")[${T(opts.footer)}]`, dctx);
    const tree = mystParse(value, {});
    for (const c of tree.children) {
      if (c.type === 'paragraph' && c.children.length === 1 && c.children[0].type === 'image') {
        emit(`${startLine(c, vBase) || findOptionLine('![', S + 1, E) || ''}`, imageBody(c.children[0].url), dctx);
      } else block(c, dctx, vBase);
    }
    return;
  }
  process.stderr.write(`WARN unhandled directive ${name} at ${S}\n`);
  sub();
}

// ---------- run ----------
const tree = mystParse(srcText, {});
blockChildren(tree.children, { indent: 0, decor: [] }, 1);

// ---------- emit typst ----------
const out = [];
out.push(`#let t(s) = s`);
out.push(`#let MONO = "DejaVu Sans Mono"`); // bundled with typst, so no font warnings on any OS
out.push(`#set page(paper: "us-letter", margin: (x: 0.8in, y: 0.9in), header: text(8pt, fill: gray)[#${q((displayName || '') + ' · copy edit copy · line numbers match ' + rel)}], footer: context align(center, text(8pt, fill: gray)[#counter(page).display() / #counter(page).final().first()]))`);
out.push(`#set text(font: "Libertinus Serif", size: 11pt, hyphenate: false)`);
out.push(`#set smartquote(enabled: false)`);
out.push(`#set par(leading: 1.25em, spacing: 0pt, justify: false)`);
out.push(`#let GAP = 1.1em`);
out.push(`#let heading-1(b) = text(size: 17pt, weight: "bold")[#b]`);
out.push(`#let heading-2(b) = text(size: 14pt, weight: "bold")[#b]`);
out.push(`#let heading-3(b) = text(size: 12pt, weight: "bold")[#b]`);
out.push(`#let heading-4(b) = text(size: 11pt, weight: "bold", style: "italic")[#b]`);
out.push(`#let doc-title(b) = text(size: 22pt, weight: "bold")[#b]`);
out.push(`#let doc-subtitle(b) = text(size: 14pt, fill: luma(90))[#b]`);
out.push(`#let doc-status(b) = text(size: 10pt, fill: luma(90))[#b]`);
out.push(`#let body-par(b) = b`);
out.push(`#let table-caption(b) = text(size: 10pt)[#b]`);
out.push(`#let fig-caption(b) = text(size: 10pt)[#b]`);
out.push(`#let tab-label(b) = text(size: 11pt, weight: "bold", fill: rgb("#1a56b0"))[#b]`);
out.push(`#let list-item(depth, mark, content) = pad(left: depth * 1.6em)[#grid(columns: (1.3em, 1fr), mark, content)]`);
out.push(`#grid(columns: (3.6em, 1fr), column-gutter: 0.7em, row-gutter: 0pt,`);
rows.forEach((r, i) => {
  const lnCell = `align(right + top, text(font: MONO, size: 8pt, fill: gray)[${r.ln}])`;
  const inner = r.indent && !/^#list-item|^#block\(width: 100%\)\[#set text/.test(r.body) ? `#pad(left: ${r.indent * 1.6}em)[${r.body.replace(/^#/, '#')}]` : r.body.startsWith('#') ? r.body : '#' + r.body;
  if (r.decor.length) {
    const d = r.decor[r.decor.length - 1];
    const prev = rows[i - 1], next = rows[i + 1];
    const same = (x) => x && x.decor.some((y) => y.id === d.id);
    const first = !same(prev), last = !same(next);
    const fill = d.type === 'adm' ? `rgb(${q(d.color + '14')})` : 'luma(247)';
    const stroke = d.type === 'adm' ? `(left: 2.5pt + rgb(${q(d.color)}))` : `(left: 2.5pt + luma(160))`;
    out.push(`  ${lnCell}, grid.cell(fill: ${fill}, stroke: ${stroke}, inset: (left: 10pt, right: 8pt, top: ${first ? '6pt' : '0pt'}, bottom: ${last ? '6pt' : 'GAP'}))[${inner}],`);
    if (last) out.push(`  [], v(GAP),`);
  } else {
    out.push(`  ${lnCell}, block(inset: (bottom: GAP))[${inner}],`);
  }
});
out.push(`)`);
fs.writeFileSync(outPath, out.join('\n') + '\n');
console.error(`rows: ${rows.length}`);
