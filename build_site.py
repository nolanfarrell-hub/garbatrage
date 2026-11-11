#!/usr/bin/env python3
"""Generate garbatrage.com from data. Run at build; commit the output."""
import json, shutil, html, re
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE = "https://garbatrage.com"

gia = json.loads((ROOT / "data/gia.json").read_text())
json_stories = json.loads((ROOT / "data/stories.json").read_text())
# Sort by date desc; ties (same-day appends) resolve by array position desc so
# the newest appended batch surfaces first on the home hero/archive.
stories = sorted(enumerate(json_stories), key=lambda p: (p[1]["date"], p[0]), reverse=True)
stories = [s for _, s in stories]
anchors = json.loads((ROOT / "data/anchors.json").read_text())
cons = gia["constituents"]

def esc(s): return html.escape(str(s), quote=True)
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:70]
def av(name): return "".join(p[0] for p in name.split()[:2]).upper()
def day(s): return datetime.fromisoformat(s).strftime("%a %d")

# Real-time tape (TradingView widget, consent-gated load; see layout <script>).
# The fiction stays in the GIA rail panel and /markets/. Terms() already names
# TradingView as a provider, so this makes the legal copy true.
TAPE_CFG = {
    "symbols": [
        {"proName": "FOREXCOM:SPXUSD", "title": "S&P 500"},
        {"proName": "FOREXCOM:NSXUSD", "title": "Nasdaq 100"},
        {"proName": "TVC:GOLD",        "title": "Gold"},
        {"proName": "TVC:USOIL",       "title": "WTI"},
        {"proName": "BITSTAMP:BTCUSD", "title": "BTC"},
        {"proName": "FX:EURUSD",       "title": "EUR/USD"},
        {"proName": "TVC:DXY",         "title": "Dollar Index"},
        {"proName": "TVC:VIX",         "title": "VIX"},
    ],
    "showSymbolLogo": False,
    "colorTheme": "dark",
    "isTransparent": True,
    "displayMode": "compact",
    "locale": "en",
}
TAPE_JSON = json.dumps(TAPE_CFG, separators=(",", ":"))

TAPE = '''<div class="tape" aria-label="Live market tape">
  <div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div></div>
  <noscript><p class="tape-noscript">Live tape needs JavaScript. The GIA — which is fiction — is on the <a href="/markets/">markets page</a>.</p></noscript>
</div>'''

CONSENT = '''<div id="gb-consent" role="region" aria-label="Cookie consent">
  <span>We use a third party for the live market tape, which may set cookies.</span>
  <div class="gbc-btns">
    <button class="gbc-ok" type="button">Accept</button>
    <button class="gbc-no" type="button">Essential only</button>
  </div>
</div>
<script data-cfasync="false">
(function () {
  var KEY = 'gb_consent';
  var want = localStorage.getItem(KEY);
  // Render the live tape by default for everyone EXCEPT likely-UK/EEA visitors,
  // who get the consent gate (TradingView sets cookies). Timezone heuristic, zero
  // third party, no infra. (IP-accurate option: a tiny Cloudflare Worker.)
  function isEea() {
    var tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
    if (/^Europe\//.test(tz)) return true;
    if (tz === 'Atlantic/Reykjavik' || tz === 'Atlantic/Canary' ||
        tz === 'Atlantic/Madeira' || tz === 'Atlantic/Azores') return true;
    return false;
  }
  function loadTape() {
    var box = document.querySelector('.tradingview-widget-container');
    if (!box) return;
    var s = document.createElement('script');
    s.type = 'text/javascript';
    s.async = true;
    s.innerHTML = '{"symbols":[{"proName":"FOREXCOM:SPXUSD","title":"S&P 500"},{"proName":"FOREXCOM:NSXUSD","title":"Nasdaq 100"},{"proName":"TVC:GOLD","title":"Gold"},{"proName":"TVC:USOIL","title":"WTI"},{"proName":"BITSTAMP:BTCUSD","title":"BTC"},{"proName":"FX:EURUSD","title":"EUR/USD"},{"proName":"TVC:DXY","title":"Dollar Index"},{"proName":"TVC:VIX","title":"VIX"}],"showSymbolLogo":false,"colorTheme":"dark","isTransparent":true,"displayMode":"compact","locale":"en"}';
    s.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js';
    box.appendChild(s);
  }
  function dismiss() {
    var b = document.getElementById('gb-consent'); if (b) b.remove();
  }
  if (isEea()) {
    if (want === 'y') { dismiss(); loadTape(); }
    else if (want === 'n') { dismiss(); }
    else {
      window.__accept = function () { localStorage.setItem(KEY, 'y'); dismiss(); loadTape(); };
      window.__decline = function () { localStorage.setItem(KEY, 'n'); dismiss(); };
      var b = document.getElementById('gb-consent');
      if (b) { b.querySelector('.gbc-ok').onclick = window.__accept; b.querySelector('.gbc-no').onclick = window.__decline; }
    }
  }
  else { dismiss(); loadTape(); } // US/rest-of-world: tape on by default, ignores stale decline
})();
</script>'''


DISC_INDEX = ('<div class="disc">Every constituent is fictional. The Garbatrage Industrial Average is a '
              'proprietary index of hand-picked mid-value securities, is not calculated by any exchange, '
              'and is not a real benchmark. Prices shown are invented. Nothing here is investment advice.</div>')
DISC_STORY = ('<div class="disc">Garbatrage is a satirical publication. Headlines, quotes, companies and '
              'figures are fabricated. Nothing here is investment advice.</div>')

def layout(title, desc, body, canonical, og_image=None, og_type="website", jsonld=None):
    ogi = (SITE + og_image) if og_image else f"{SITE}/assets/og-card.png"
    ld = jsonld or {}
    ld_block = ld.get("block") or (
        '<script type="application/ld+json">'
        + json.dumps({
            "@context": "https://schema.org",
            "@type": ld.get("type", "WebPage"),
            "name": ld.get("name", title),
            "description": desc,
            "url": f"{SITE}{canonical.replace(SITE,'') if canonical.startswith(SITE) else canonical}",
            "publisher": {
                "@type": "Organization",
                "name": "Garbatrage Media Group LLC",
                "url": SITE,
                "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo-cream.png"},
            },
        }, ensure_ascii=False)
        + "</script>"
    )
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{ogi}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/favicon-180.png">
<link rel="me" href="https://twitter.com/garbatrage">
<link rel="me" href="https://warpcast.com/garbatrage">
<meta name="theme-color" content="#0e2540">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
{ld_block}
</head><body><a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<header class="bar"><a href="/" class="wordmark" aria-label="Garbatrage — home"><img class="mark" src="/assets/logo-g-vector.svg" alt="G" width="24" height="28">Garbatrage</a><nav class="back"><a href="/markets/">Markets</a> · <a href="/desk/">The Desk</a> · <a href="/archive/">Archive</a></nav></header>
{TAPE}
<main id="main">{body}</main>
</div>
{CONSENT}
</body></html>"""

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
def img(s):
    return s.get("image") or f'/media/img/{s["slug"]}.png'

def build_story(s):
    art = img(s)
    url = f"{SITE}/story/{s['slug']}/"
    share = (f'<div class="share"><a href="https://twitter.com/intent/tweet?text={quote(s["title"])}&url={quote(url)}" target="_blank" rel="noopener">Post to X</a>'
             f'<a href="https://warpcast.com/~/compose?text={quote(s["title"])}&embeds[]={quote(url)}" target="_blank" rel="noopener">Cast</a>'
             f'<a href="{esc(url)}" data-copy>Copy link</a></div>')
    jsonld = {
        "type": "NewsArticle",
        "name": s["title"],
        "block": ('<script type="application/ld+json">'
                  + json.dumps({
                      "@context": "https://schema.org",
                      "@type": "NewsArticle",
                      "headline": s["title"],
                      "description": s["dek"],
                      "datePublished": s["date"],
                      "dateModified": s["date"],
                      "author": {"@type": "Person", "name": s["author"]},
                      "publisher": {"@type": "Organization", "name": "Garbatrage Media Group LLC",
                                    "url": SITE,
                                    "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo-cream.png"}},
                      "image": [f"{SITE}{art}"],
                      "url": url,
                      "mainEntityOfPage": url,
                  }, ensure_ascii=False)
                  + "</script>"),
    }
    body = f"""
<div class="kick">{esc(s["desk"])}</div>
<h1>{esc(s["title"])}</h1>
<p class="lede">{esc(s["dek"])}</p>
<figure class="artbox"><img class="art-img" src="{art}" alt="" loading="lazy"></figure>
<div class="byline"><span class="av">{esc(s.get("av") or av(s["author"]))}</span>
<span><b>{esc(s["author"])}</b><br>{esc(s.get("role", ""))}</span>
<span class="rd"><time datetime="{esc(s["date"])}">{esc(s["date"])}</time> · {s.get("read", 4)} min read</span></div>
<article class="art">{s["body"]}</article>
<div class="tags">{"".join(f'<span class="chip">{esc(t)}</span>' for t in s.get("tags", []))}</div>
{share}
{DISC_STORY}
<div class="pager"><a href="/archive/">← Archive</a><span>{esc(s["date"])}</span><a href="/">Home</a></div>"""
    write(f"story/{s['slug']}/index.html",
          layout(f"{s['title']} · Garbatrage", s["dek"], body, url, og_image=art,
                 og_type="article", jsonld=jsonld))

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

# ---------- markets (sectors folded in as in-page anchors; no thin /sector/*/ pages) ----------
def listing(groups, active="all"):
    chips = '<a href="#all"' + (' class="on"' if active == "all" else "") + '>All</a>'
    chips += "".join(
        f'<a href="#{slugify(s)}"' + (' class="on"' if slugify(s) == slugify(active) else "") + f'>{esc(s)}</a>'
        for s in gia["sectors"])
    blocks = ""
    for sector, rows in groups:
        trs = "".join(
            f'<tr><td class="t">{esc(c["ticker"])}</td>'
            f'<td class="nm"><a href="/company/{c["ticker"].lower()}/">{esc(c["name"])}</a></td>'
            f'<td class="cap">{esc(c["cap"])}</td><td class="px">${c["price"]}</td>'
            f'<td class="ch {"up" if c["change"] >= 0 else "dn"}">{c["change"]:+.1f}%</td></tr>'
            for c in rows)
        blocks += (f'<h2 id="{slugify(sector)}">{esc(sector)} <span>{len(rows)} of {len(cons)}</span></h2>'
                   f'<table>{trs}</table>')
    body = f"""<div class="kick">Markets · Index Construction</div><h1>The Garbatrage Industrial Average</h1>
<p class="lede">Twenty-five constituents, hand-picked, weighted by price and by mood. Every market is fictional; the construction is the point.</p>
<div class="summary"><b>38,221.07</b><span class="ch dn">▼ 321.44 (-0.83%)</span><span class="n">Fictional index</span></div>
<div class="chips">{chips}</div>{blocks}{DISC_INDEX}"""
    write("markets/index.html",
          layout("Markets · Garbatrage", "Twenty-five constituents, hand-picked, weighted by price and by mood.", body, f"{SITE}/markets/"))

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
    urls = [f"{SITE}/", f"{SITE}/markets/", f"{SITE}/archive/", f"{SITE}/desk/", f"{SITE}/about/",
            f"{SITE}/methodology/", f"{SITE}/terms.html", f"{SITE}/privacy.html"]
    urls += [f"{SITE}/company/{c['ticker'].lower()}/" for c in cons]
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
# Rotating quote pool — all eight anchors in the fiction, plus the man-on-the-street
# register. Every quote is fabricated; the rotating pick (by day-of-ordinal) means the
# displayed byline changes, not just the words.
QUOTES = [
    ("Diversification is the practice of making every mistake at once, and then being unable to blame a single one, which we regard as the whole of risk management.",
     "Elena Marsh", "Head of Research"),
    ("We are asked constantly what we are selling. The honest answer is the thesis, which we sold to ourselves two quarters ago at a premium.",
     "Dana Whitfield", "Portfolio Strategy"),
    ("The market does not want a decision; it wants a building that has not decided.",
     "Marcus Reid", "Markets Anchor · NYSE Floor"),
    ("A rate cut is not the answer; it is the answer to a question nobody has stopped to ask, which is a different job entirely.",
     "Priya Sharma", "Washington Bureau · Fed & Rates"),
    ("The economy is not a forecast; it is a weather report delivered to people who have already gone outside.",
     "Tessa Nguyen", "Economy & Data Reporter"),
    ("Vesting is the only clause a board reads twice. It is also the only one that reads the board back.",
     "Omar Zayed", "Corporate Governance Desk"),
    ("Before the open, nothing has happened and everyone is fully briefed on it, which is the cleanest the market ever looks.",
     "Jake Sullivan", "Breakfast Anchor · Before The Open"),
    ("Yield is a language and the market is bilingual, but it may be lying in the language you do not speak.",
     "Claire Reyes", "Debt & Fixed Income"),
    ("The state says I should feel something, and I do, but my advisor has already bought the feeling for me at a discount.",
     "Chandra Ferrara", "Drawer Slider, Trust & Estates", "street"),
    ("I have some outstanding parking tickets if the Fed is taking those, too.",
     "Tim Llanas", "Snake Farmer, Private Wealth", "street"),
    ("Are the rate cut leftovers up for grabs, then? I have an account that has been fasting since the last one.",
     "Scott Dutreix", "Darts Referee, Rates Desk", "street"),
    ("I do not act on the news; I have a person who acts on the news, and the person is a filing cabinet that is not hiring.",
     "Avery Loomis", "General Partner, Inertia Fund", "street"),
]

# Fresh daily quotes: the daily refresh SOP writes today's three vetted, freshly-written
# quotes to data/home_quotes.json ([{text,name,role,street?} x3]). When that file exists,
# build_home uses it verbatim; when absent (e.g. a manual rebuild), fall back to the pool.
_HOME_QUOTES_PATH = ROOT / "data" / "home_quotes.json"
def _home_quotes():
    p = _HOME_QUOTES_PATH
    if not p.exists():
        return None
    import json as _json
    try:
        qs = _json.loads(p.read_text())
    except Exception:
        return None
    if not isinstance(qs, list) or len(qs) < 3:
        return None
    out = []
    for q in qs[:3]:
        if not (isinstance(q, dict) and q.get("text") and q.get("name")):
            return None
        out.append((q["text"], q["name"], q.get("role", ""), "street" if q.get("street") else None))
    return out

FOOTER = """<footer><div class="fg">
<div><h4>Markets</h4><a href="/markets/">Indexes</a><a href="/archive/">Archive</a><a href="/desk/">The Desk</a></div>
<div><h4>Company</h4><a href="/about/">About</a><a href="/press/">Press</a><a href="mailto:info@garbatrage.com">Contact</a></div>
<div><h4>Resources</h4><a href="/methodology/">Methodology</a><a href="/archive/">All stories</a><a href="/rss.xml">RSS</a></div>
<div><h4>Legal</h4><a href="/terms.html">Terms</a><a href="/privacy.html">Privacy</a></div>
</div><div class="legal">GARBATRAGE is a satirical publication presented in the style of a professional financial news desk.
All quotes, indexes, tickers and figures are fabricated; any resemblance to real securities, people or firms is coincidental.
Nothing herein is investment, legal or tax advice. © Garbatrage Media Group LLC. Not a registered investment adviser.
Garbatrage Media Group LLC · <a href="mailto:info@garbatrage.com">info@garbatrage.com</a></div></footer>
<script data-cfasync="false">document.querySelectorAll('[data-copy]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();navigator.clipboard.writeText(a.href).then(function(){a.textContent='Copied';});});});</script>"""

def build_home():
    lead = stories[0]
    briefs = stories[1:7]
    movers = sorted(cons, key=lambda c: c["change"], reverse=True)[:3]
    # Weighted rotation: street voices double-weighted (50% of days) so the
    # man-on-the-street register keeps showing, interleaved so no two adjacent
    # slots are the same voice (no back-to-back repeats as the date advances).
    _anchors = [e for e in QUOTES if not (len(e) > 3 and e[3] == "street")]
    _streets = [e for e in QUOTES if len(e) > 3 and e[3] == "street"]
    _pool = []
    for i in range(len(_anchors) + len(_streets)):
        if i % 2 == 0:
            _pool.append(_anchors[(i // 2) % len(_anchors)])
        else:
            _pool.append(_streets[(i // 2) % len(_streets)])
    _q = _pool[datetime.now().toordinal() % len(_pool)]
    q, qn, qr = _q[:3]
    kind = _q[3] if len(_q) > 3 else None
    # Rail shows THREE distinct quote voices (day-keyed), not just today's one.
    # Prefer today's fresh vetted quotes (data/home_quotes.json); fall back to the pool.
    _fresh = _home_quotes()
    def _pick(offset):
        e = _pool[(datetime.now().toordinal() + offset) % len(_pool)]
        return e[0], e[1], e[2], (e[3] if len(e) > 3 else None)
    if _fresh:
        _three = list(_fresh)
    else:
        _three = []
        _ord = datetime.now().toordinal()
        _n = 0
        while len(_three) < 3 and _n < len(_pool):
            e = _pool[(_ord + _n) % len(_pool)]
            name = e[1]
            if not any(x[0] == name for x in _three):
                _three.append((e[0], e[1], e[2], e[3] if len(e) > 3 else None))
            _n += 1
    quotes_html = "".join(
        f'<div class="quote">“{esc(x[0])}”<i>{esc(x[1])}{", " if x[3] == "street" else " · "}{esc(x[2])}</i></div>'
        for x in _three)
    rail_rows = "".join(
        f'<div class="row"><span>{esc(c["ticker"])}</span>'
        f'<b class="{"up" if c["change"] >= 0 else "dn"}">{c["change"]:+.1f}%</b></div>'
        for c in movers)
    brief_html = "".join(
        f'<a class="item" href="/story/{s["slug"]}/"><div class="thumb"><img src="{img(s)}" alt="" loading="lazy"></div><div>'
        f'<h3>{esc(s["title"])}</h3><p>{esc(s["dek"])}</p>'
        f'<div class="meta">{esc(s["desk"])} · {esc(s["author"])}</div></div></a>'
        for s in briefs)
    body = f"""
<div class="home">
<div class="col">
  <div class="kick">{esc(lead["desk"])}</div>
  <h1><a href="/story/{lead["slug"]}/">{esc(lead["title"])}</a></h1>
  <p class="dek">{esc(lead["dek"])}</p>
  <a class="hero" href="/story/{lead["slug"]}/"><img src="{img(lead)}" alt="" loading="lazy"></a>
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
  {quotes_html}
</aside>
</div>
<div class="news"><div class="nin">
  <div><h2>The Morning Dump</h2><p>Six headlines and one quietly mispriced thing, every weekday at 6:40.</p></div>
  <a class="btn" href="mailto:info@garbatrage.com?subject=Subscribe%20to%20The%20Morning%20Dump&body=Add%20me%20to%20the%20list.%20Address%20to%20use%3A%20">Subscribe</a>
</div></div>
{FOOTER}"""
    write("index.html",
          layout("Garbatrage · Markets. Money. Mischief.",
                 "Deadpan financial satire. A fictional market, reported straight, every weekday.",
                 body, f"{SITE}/"))

# ---------- desks ----------
DESKS = ["markets", "rates", "etfs", "hauling", "earnings", "estate"]

def build_desk(desk):
    rows = "".join(
        f'<div class="entry"><div class="d">{day(s["date"])}</div>'
        f'<a href="/story/{s["slug"]}/"><h3>{esc(s["title"])}</h3>'
        f'<div class="m">{esc(s["author"])}</div></a></div>'
        for s in stories if s["desk"].lower() == desk)
    label = desk.capitalize()
    body = (f'<div class="kick">Desk</div><h1>{label}</h1>'
            f'<p class="lede">Every piece filed to the {label} desk.</p>'
            f'{rows or "<p>Nothing filed yet.</p>"}{DISC_INDEX}')
    write(f"desk/{desk}/index.html",
          layout(f"{label} · Garbatrage", f"{label} coverage from Garbatrage.",
                 body, f"{SITE}/desk/{desk}/"))

def build_roster():
    # rotate the display order daily so the roster isn't static; the roster card is
    # authored in data/anchors.json order and the rotation starts fresh each build.
    order = anchors[datetime.now().toordinal() % len(anchors):] + anchors[:datetime.now().toordinal() % len(anchors)]
    cards = "".join(
        f'<div class="anchor"><div class="an-av">{av(a["name"])}</div>'
        f'<div class="an-nm">{esc(a["name"])}</div>'
        f'<div class="an-role">{esc(a["role"])}</div>'
        f'<p class="an-bio">{esc(a["bio"])}</p>'
        f'<div class="an-filed">{sum(1 for s in stories if s["author"] == a["name"])} pieces filed</div></div>'
        for a in order)
    body = (f'<div class="kick">The Desk</div><h1>Who files.</h1>'
            f'<p class="lede">Eight bylines, one desk, no real people. Every one of them is invented and every one of them would tell you otherwise.</p>'
            f'<div class="roster">{cards}</div>'
            f'<p class="lede" style="margin-top:22px">All eight are fictional. The work is not.</p>{DISC_INDEX}')
    write("desk/index.html",
          layout("The Desk · Garbatrage", "The Garbatrage anchor roster — eight fictional bylines.",
                 body, f"{SITE}/desk/"))

# ---------- run ----------
if OUT.exists():
    shutil.rmtree(OUT)
for s in stories:
    build_story(s)
for i, c in enumerate(cons):
    build_company(c, i)
listing([(s, [c for c in cons if c["sector"] == s]) for s in gia["sectors"]])
build_archive()
build_home()
build_roster()
build_feeds()
shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
# media/ (story illustration PNGs) lives outside static/; carry it into the build so
# `rm -rf site && build` cannot silently drop the images.
if (ROOT / "media").exists():
    if (OUT / "media").exists():
        shutil.rmtree(OUT / "media")
    shutil.copytree(ROOT / "media", OUT / "media")
print(f"built {len(stories)} stories, {len(cons)} companies, {len(gia['sectors'])} sectors, media carried")