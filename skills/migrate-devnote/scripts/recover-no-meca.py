"""Rebuild a DevNote source tree from the venue's published assets.

Use when an article has no MECA archive. The site publishes every asset under
pub.curvenote.com/<siteId>/public/ with its stem truncated to 20 characters and
a content hash appended, so the original paths must come from main.md.
"""
import json, os, re, sys, urllib.request

def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(r).read()

def main(article_slug, out_dir):
    page = get(f"https://devnotes.nucleus.engineering/articles/{article_slug}").decode()
    assets = sorted({u.rstrip(')"\'') for u in
                     re.findall(r'https://pub\.curvenote\.com/[^"\')\s]+', page)})
    base = re.match(r'(https://pub\.curvenote\.com/[^/]+)/', assets[0]).group(1)
    cfg = json.loads(get(f"{base}/config.json"))
    proj = cfg["projects"][0]

    # published basename -> url
    pub = {}
    for u in assets:
        if "/public/" not in u:
            continue
        pub[u.rsplit("/", 1)[1]] = u

    md_url = next(u for n, u in pub.items() if n.startswith("main-") and n.endswith(".md"))
    md = get(md_url).decode()
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "main.md"), "w").write(md)

    # every local path main.md points at, ignoring anything the author
    # commented out — a disabled figure is not missing content
    live = re.sub(r'<!--.*?-->', '', md, flags=re.S)
    refs = set()
    for pat in (r'^:::+\{(?:figure|image)\}\s+(\S+)\s*$', r'\]\((\./[^)\s]+)\)'):
        refs |= set(re.findall(pat, live, re.M))
    disabled = set()
    for c in re.findall(r'<!--.*?-->', md, flags=re.S):
        disabled |= set(re.findall(r'^:::+\{(?:figure|image)\}\s+(\S+)\s*$', c, re.M))
    banner = proj.get("banner")
    thumb = proj.get("thumbnail")
    for extra in (banner, thumb):
        if extra:
            refs.add(extra)

    def published_name(stem, ext):
        """The site truncates a stem to 20 chars before appending its hash."""
        if stem + ext in pub:      # banner/thumbnail already carry the hash
            return stem + ext
        want = stem[:20]
        hits = [n for n in pub if n.startswith(want + "-") and n.endswith(ext)]
        return hits[0] if len(hits) == 1 else None

    got, missing = [], []
    for ref in sorted(refs):
        rel = ref.lstrip("/")
        if rel.startswith("./"):
            rel = rel[2:]
        stem, ext = os.path.splitext(os.path.basename(rel))
        name = published_name(stem, ext)
        if not name:
            missing.append(ref)
            continue
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        open(dest, "wb").write(get(pub[name]))
        got.append((ref, name))

    unused = set(pub) - {n for _, n in got} - {md_url.rsplit("/", 1)[1]}
    print(f"=== {article_slug} -> {out_dir}")
    print(f"    work key : {proj.get('id')}")
    print(f"    title    : {proj.get('title')}")
    print(f"    toc      : {[t.get('file') for t in proj.get('toc', [])]}")
    for ref, name in got:
        print(f"    ok       {ref}  <- {name}")
    for ref in missing:
        print(f"    *** UNRESOLVED {ref}")
    for n in sorted(unused):
        print(f"    (published but unreferenced) {n}")
    json.dump(proj, open(os.path.join(out_dir, "_config-project.json"), "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
