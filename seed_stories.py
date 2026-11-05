#!/usr/bin/env python3
"""One-time: build data/stories.json from story/*.html with honest git dates.
Run once. Afterwards the daily refresh appends; never re-run this."""
import json, re, subprocess, html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
OUT = ROOT / "data/stories.json"
SRC = ROOT / "story"

def git_date(f):
    r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%aI", "--", str(f)],
                       capture_output=True, text=True)
    stamps = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    return stamps[-1] if stamps else None

def text(h):
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:70]

def parse_body(raw):
    """Pick the article content out of a story page regardless of wrapper.
    New-format pages use <article class=\"art\">…</article>; legacy build_story_pages
    files use <main class=\"story-main\">… <div><p class=\"lead\">…<div class=\"a-tags\">."""
    m = re.search(r'<article[^>]*>(.*?)</article>', raw, re.S)
    if m:
        inner = m.group(1)
    else:
        # legacy: the <div> following the byline, before a-tags
        m2 = re.search(r'<div class="a-byline">.*?</div>\s*(?:<img[^>]*>\s*)?<div>(.*?)</div>\s*<div class="a-tags"', raw, re.S)
        inner = m2.group(1) if m2 else ""
    paras = re.findall(r"<p[^>]*>(.*?)</p>", inner, re.S) or [inner]
    return "".join(f"<p>{p.strip()}</p>" for p in paras if text(p))

def parse(p):
    raw = p.read_text(encoding="utf-8", errors="ignore")
    t = re.search(r"<title>(.*?)(?:\s*·\s*Garbatrage)?</title>", raw, re.S)
    if not t:
        return None
    title = html.unescape(t.group(1)).strip()
    if not title or title.lower() == "garbatrage":
        return None
    d = re.search(r'<meta\s+name="description"\s+content="(.*?)"', raw, re.S)
    dek = html.unescape(d.group(1)).strip() if d else ""
    html_body = parse_body(raw)
    by = re.search(r'class="[^"]*a-name[^"]*"[^>]*>(.*?)<', raw)
    role = re.search(r'class="[^"]*a-role[^"]*"[^>]*>(.*?)<', raw)
    cat = re.search(r'class="[^"]*a-cat[^"]*"[^>]*>(.*?)<', raw)
    return {
        "title": title,
        "dek": dek or text(html_body)[:180],
        "slug": slug(title),
        "desk": text(cat.group(1)) if cat else "Markets",
        "author": text(by.group(1)) if by else "Marcus Reid",
        "role": text(role.group(1)) if role else "",
        "body": html_body,
        "tags": [],
    }

seen, out = set(), []
for p in sorted(SRC.glob("*.html")):
    e = parse(p)
    if not e or e["slug"] in seen:
        continue
    d = git_date(p)
    if not d:
        print(f"skip (no git date): {p.name}")
        continue
    e["date"] = d[:10]
    e["read"] = max(2, len(text(e["body"]).split()) // 200)
    seen.add(e["slug"])
    out.append(e)

out.sort(key=lambda s: s["date"])
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"wrote {len(out)} stories -> {OUT}")
