#!/usr/bin/env python3
"""Generate garbatrage.com from data. Run at build; commit the output."""
import json, shutil, html, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE = "https://garbatrage.com"

gia = json.loads((ROOT / "data/gia.json").read_text())
stories = sorted(json.loads((ROOT / "data/stories.json").read_text()),
                 key=lambda s: s["date"], reverse=True)
cons = gia["constituents"]

def esc(s): return html.escape(str(s), quote=True)
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:70]
def av(name): return "".join(p[0] for p in name.split()[:2]).upper()
def day(s): return datetime.fromisoformat(s).strftime("%a %d")

TAPE = "".join(
    f'<span><i class="s">{esc(c["ticker"])}</i> {c["price"]} '
    f'<i class="{"up" if c["change"] >= 0 else "dn"}">{c["change"]:+.1f}%</i></span>'
    for c in cons[:8])

DISC_INDEX = ('<div class="disc">Every constituent is fictional. The Garbatrage Industrial Average is a '
              'proprietary index of hand-picked mid-value securities, is not calculated by any exchange, '
              'and is not a real benchmark. Prices shown are invented. Nothing here is investment advice.</div>')
DISC_STORY = ('<div class="disc">Garbatrage is a satirical publication. Headlines, quotes, companies and '
              'figures are fabricated. Nothing here is investment advice.</div>')

def layout(title, desc, body, canonical):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/assets/og-card.png">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/favicon-180.png">
<meta name="theme-color" content="#141414">
<link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
</head><body><div class="wrap">
<div class="bar"><a href="/">Garbatrage</a><span class="back"><a href="/markets/">Markets</a> · <a href="/archive/">Archive</a></span></div>
<div class="tape">{TAPE}</div>
{body}
</div></body></html>"""

def pager(prev, nxt, label):
    left = (f'<a href="/company/{prev["ticker"].lower()}/">← {esc(prev["ticker"])}</a>'
            if prev else "<span>←</span>")
    right = (f'<a href="/company/{nxt["ticker"].lower()}/">{esc(nxt["ticker"])} →</a>'
             if nxt else "<span>→</span>")
    return f'<div class="pager">{left}<span>{label}</span>{right}</div>'

def write(rel, content, raw=False):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ---------- stories ----------
def build_story(s):
    body = f"""
<div class="kick">{esc(s["desk"])}</div>
<h1>{esc(s["title"])}</h1>
<p class="lede">{esc(s["dek"])}</p>
<div class="byline"><span class="av">{esc(s.get("av") or av(s["author"]))}</span>
<span><b>{esc(s["author"])}</b><br>{esc(s.get("role", ""))}</span>
<span class="rd">{s.get("read", 4)} min read</span></div>
<article class="art">{s["body"]}</article>
<div class="tags">{"".join(f'<span class="chip">{esc(t)}</span>' for t in s.get("tags", []))}</div>
{DISC_STORY}
<div class="pager"><a href="/archive/">← Archive</a><span>{esc(s["date"])}</span><a href="/">Home</a></div>"""
    url = f"{SITE}/story/{s['slug']}/"
    write(f"story/{s['slug']}/index.html",
          layout(f"{s['title']} · Garbatrage", s["dek"], body, url))

# ---------- companies ----------
def build_company(c, i):
    prev_c = cons[i - 1] if i else None
    next_c = cons[i + 1] if i + 1 < len(cons) else None
    filings = "".join(
        f'<li><span>{esc(f["type"])} · {esc(f["when"])}</span>{esc(f["text"])}</li>'
        for f in c.get("filings", []))
    body = f"""
<div class="kick">{esc(c["sector"])} · GIA Constituent</div>
<h1>{esc(c["name"])}</h1>
<div class="price"><b>${c["price"]}</b><span class="ch {"up" if c["change"] >= 0 else "dn"}">{c["change"]:+.1f}%</span><span class="tick">{esc(c["ticker"])}</span></div>
<p class="lede">{esc(c["lede"])}</p>
<table>
<tr><th>Ticker</th><td>{esc(c["ticker"])}</td></tr>
<tr><th>Sector</th><td>{esc(c["sector"])}</td></tr>
<tr><th>Market cap</th><td>{esc(c["cap"])}</td></tr>
<tr><th>Chief executive</th><td>{esc(c["ceo"])}</td></tr>
<tr><th>Founded</th><td>{c["founded"]}</td></tr>
<tr><th>Headquarters</th><td>{esc(c["hq"])}</td></tr>
</table>
<h2>Business</h2><p>{esc(c["business"])}</p>
<div class="quote">“{esc(c["quote"])}”<i>{esc(c["ceo"])} · Chief Executive</i></div>
<h2>Recent filings</h2><ul class="fil">{filings}</ul>
{DISC_INDEX}{pager(prev_c, next_c, f"Constituent {i + 1} of {len(cons)}")}"""
    url = f"{SITE}/company/{c['ticker'].lower()}/"
    write(f"company/{c['ticker'].lower()}/index.html",
          layout(f"{c['name']} ({c['ticker']}) · Garbatrage",
                 f"{c['name']} — {c['sector']} constituent of the Garbatrage Industrial Average. Fictional.",
                 body, url))

# ---------- markets + sectors ----------
def listing(title, desc, groups, url, active):
    chips = '<a href="/markets/"' + (' class="on"' if active == "all" else "") + '>All</a>'
    chips += "".join(
        f'<a href="/{slugify(s)}/"' + (' class="on"' if slugify(s) == slugify(active) else "") + f'>{esc(s)}</a>'
        for s in gia["sectors"])
    blocks = ""
    for sector, rows in groups:
        trs = "".join(
            f'<tr><td class="t">{esc(c["ticker"])}</td>'
            f'<td class="nm"><a href="/company/{c["ticker"].lower()}/">{esc(c["name"])}</a></td>'
            f'<td class="cap">{esc(c["cap"])}</td><td class="px">${c["price"]}</td>'
            f'<td class="ch {"up" if c["change"] >= 0 else "dn"}">{c["change"]:+.1f}%</td></tr>'
            for c in rows)
        blocks += (f'<h2>{esc(sector)} <span>{len(rows)} of {len(cons)}</span></h2>'
                   f'<table>{trs}</table>')
    body = f"""<div class="kick">Markets · Index Construction</div><h1>{esc(title)}</h1>
<p class="lede">{esc(desc)}</p>
<div class="summary"><b>38,221.07</b><span class="ch dn">▼ 321.44 (-0.83%)</span><span class="n">Fictional index</span></div>
<div class="chips">{chips}</div>{blocks}{DISC_INDEX}"""
    write(("markets" if active == "all" else slugify(active)) + "/index.html",
          layout(f"{title} · Garbatrage", desc, body, url))

# ---------- archive ----------
def build_archive():
    buckets = {}
    for s in stories:
        buckets.setdefault(s["date"][:7], []).append(s)
    out = ""
    for month in sorted(buckets, reverse=True):
        rows = "".join(
            f'<div class="entry"><div class="d">{day(s["date"])}</div>'
            f'<a href="/story/{s["slug"]}/"><h3>{esc(s["title"])}</h3>'
            f'<div class="m"><b>{esc(s["desk"])}</b> · {esc(s["author"])}</div></a></div>'
            for s in buckets[month])
        label = datetime.fromisoformat(month + "-01").strftime("%B %Y")
        out += f'<h2>{label} <span>{len(buckets[month])} pieces</span></h2>{rows}'
    body = (f'<div class="kick">Archive</div><h1>Everything we have published.</h1>'
            f'<p class="lede">Newest first, by month and desk. Nothing is deleted.</p>{out}{DISC_INDEX}')
    write("archive/index.html",
          layout("Archive · Garbatrage", "Every piece Garbatrage has published, by month and desk.",
                 body, f"{SITE}/archive/"))

# ---------- feeds ----------
def build_feeds():
    urls = [f"{SITE}/", f"{SITE}/markets/", f"{SITE}/archive/", f"{SITE}/about/",
            f"{SITE}/methodology/", f"{SITE}/terms.html", f"{SITE}/privacy.html"]
    urls += [f"{SITE}/company/{c['ticker'].lower()}/" for c in cons]
    urls += [f"{SITE}/{slugify(s)}/" for s in gia["sectors"]]
    urls += [f"{SITE}/story/{s['slug']}/" for s in stories]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
          + "</urlset>", raw=True)
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", raw=True)
    items = "".join(
        f"<item><title>{esc(s['title'])}</title><link>{SITE}/story/{s['slug']}/</link>"
        f"<guid>{SITE}/story/{s['slug']}/</guid>"
        f"<pubDate>{datetime.fromisoformat(s['date']).strftime('%a, %d %b %Y 06:40:00 +0000')}</pubDate>"
        f"<description>{esc(s['dek'])}</description></item>" for s in stories[:40])
    write("rss.xml",
          f'<?xml version="1.0"?><rss version="2.0"><channel><title>Garbatrage</title>'
          f'<link>{SITE}/</link><description>Markets. Money. Mischief.</description>{items}</channel></rss>',
          raw=True)

# ---------- home ----------
QUOTES = [
    ("Diversification is the practice of making every mistake at once, and then being unable to blame a single one, which we regard as the whole of risk management.",
     "Elena Marsh", "Head of Research"),
    ("We are asked constantly what we are selling. The honest answer is the thesis, which we sold to ourselves two quarters ago at a premium.",
     "Dana Whitfield", "Portfolio Strategy"),
    ("The market does not want a decision; it wants a building that has not decided.",
     "Marcus Reid", "Markets Anchor"),
]

FOOTER = """<footer><div class="fg">
<div><h4>Markets</h4><a href="/markets/">Indexes</a><a href="/archive/">Archive</a><a href="/rates/">Rates</a></div>
<div><h4>Company</h4><a href="/about/">About</a><a href="/press/">Press</a><a href="mailto:info@garbatrage.com">Contact</a></div>
<div><h4>Resources</h4><a href="/methodology/">Methodology</a><a href="/archive/">All stories</a><a href="/rss.xml">RSS</a></div>
<div><h4>Legal</h4><a href="/terms.html">Terms</a><a href="/privacy.html">Privacy</a></div>
</div><div class="legal">GARBATRAGE is a satirical publication presented in the style of a professional financial news desk.
All quotes, indexes, tickers and figures are fabricated; any resemblance to real securities, people or firms is coincidental.
Nothing herein is investment, legal or tax advice. © Garbatrage Media Group LLC. Not a registered investment adviser.</div></footer>"""

def build_home():
    lead = stories[0]
    briefs = stories[1:7]
    movers = sorted(cons, key=lambda c: c["change"], reverse=True)[:3]
    q, qn, qr = QUOTES[datetime.now().toordinal() % len(QUOTES)]
    rail_rows = "".join(
        f'<div class="row"><span>{esc(c["ticker"])}</span>'
        f'<b class="{"up" if c["change"] >= 0 else "dn"}">{c["change"]:+.1f}%</b></div>'
        for c in movers)
    brief_html = "".join(
        f'<a class="item" href="/story/{s["slug"]}/"><div class="thumb"></div><div>'
        f'<h3>{esc(s["title"])}</h3><p>{esc(s["dek"])}</p>'
        f'<div class="meta">{esc(s["desk"])} · {esc(s["author"])}</div></div></a>'
        for s in briefs)
    body = f"""
<main class="home">
<div class="col">
  <div class="kick">{esc(lead["desk"])}</div>
  <h1><a href="/story/{lead["slug"]}/">{esc(lead["title"])}</a></h1>
  <p class="dek">{esc(lead["dek"])}</p>
  <a class="hero" href="/story/{lead["slug"]}/"></a>
  <div class="by"><span class="av">{esc(lead.get("av") or av(lead["author"]))}</span>
    <span><b>{esc(lead["author"])}</b> · {esc(lead.get("role", ""))} · {lead.get("read", 4)} min read</span></div>
  <div class="sec">Markets Brief</div>
  {brief_html}
</div>
<aside class="rail">
  <div class="panel">
    <div class="ph"><span>Garbatrage Industrial Avg</span><span>GIA</span></div>
    <div class="pb">
      <div class="big">38,221.07 <span>▼321.44 (-0.83%)</span></div>
      <div class="sub">Down on mixed hauling volumes</div>
      <div style="margin-top:10px">{rail_rows}</div>
    </div>
    <div class="disc">GIA is a proprietary index of hand-picked mid-value securities. Not a real benchmark. Not investment advice.</div>
  </div>
  <div class="quote">“{esc(q)}”<i>{esc(qn)} · {esc(qr)}</i></div>
</aside>
</main>
<div class="news"><div class="nin">
  <div><h2>The Morning Dump</h2><p>Six headlines and one quietly mispriced thing, every weekday at 6:40.</p></div>
  <form action="/subscribe" method="post">
    <input type="email" name="email" placeholder="you@work.com" required aria-label="Email">
    <button type="submit">Subscribe</button>
  </form>
</div></div>
{FOOTER}"""
    write("index.html",
          layout("Garbatrage · Markets. Money. Mischief.",
                 "Deadpan financial satire. A fictional market, reported straight, every weekday.",
                 body, f"{SITE}/"))

# ---------- run ----------
if OUT.exists():
    shutil.rmtree(OUT)
for s in stories:
    build_story(s)
for i, c in enumerate(cons):
    build_company(c, i)
listing("The Garbatrage Industrial Average",
        "Twenty-five constituents, hand-picked, weighted by price and by mood.",
        [(s, [c for c in cons if c["sector"] == s]) for s in gia["sectors"]],
        f"{SITE}/markets/", "all")
for s in gia["sectors"]:
    listing(s, f"{s} constituents of the Garbatrage Industrial Average.",
            [(s, [c for c in cons if c["sector"] == s])],
            f"{SITE}/{slugify(s)}/", s)
build_archive()
build_home()
build_feeds()
shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
print(f"built {len(stories)} stories, {len(cons)} companies, {len(gia['sectors'])} sectors")