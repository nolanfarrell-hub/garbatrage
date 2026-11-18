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
def vol(s): return datetime.fromisoformat(s).strftime("%Y")

# Real-time tape (TradingView widget, consent-gated load; see layout <script>).
# The fiction stays in the GIA rail panel and /markets/. Terms() already names
# TradingView as a provider, so this makes the legal copy true.
from site_tape import TAPE_CFG
TAPE_JSON = json.dumps(TAPE_CFG, separators=(",", ":"))

TAPE = '''<div class="tape" aria-label="Live market tape">
  <div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div></div>
  <noscript><p class="tape-noscript">Live tape needs JavaScript. The GIA — which is fiction — is in the panel and on the <a href="/markets/">markets page</a>.</p></noscript>
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
    s.innerHTML = '__TAPE_JSON__';
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
  // Newsletter capture — POST to the worker /subscribe, show a result in place.
  document.querySelectorAll('form[data-subscribe]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var msg = f.querySelector('.submsg');
      var btn = f.querySelector('button');
      var email = f.querySelector('input[name="email"]');
      if (!email || !email.value || !/.+@.+\..{2,}/.test(email.value)) { if (msg) msg.textContent = 'Enter a real email.'; return; }
      btn.disabled = true;
      fetch(f.action, { method: 'POST', body: new FormData(f) })
        .then(function (r) {
          if (r.ok) { if (msg) msg.textContent = 'You are on the list. The Dump comes to you.'; f.reset(); }
          else { if (msg) msg.textContent = 'Could not sign you up — try again.'; }
        })
        .catch(function () { if (msg) msg.textContent = 'Could not sign you up — try again.'; })
        .finally(function () { btn.disabled = false; });
    });
  });
})();
</script>'''


DISC_INDEX = ('<div class="disc">Every constituent is fictional. The Garbatrage Industrial Average is a '
              'proprietary index of hand-picked mid-value securities, is not calculated by any exchange, '
              'and is not a real benchmark. Prices shown are invented. Nothing here is investment advice.</div>')
DISC_STORY = ('<div class="disc">Garbatrage is a satirical publication. Headlines, quotes, companies and '
              'figures are fabricated. Nothing here is investment advice.</div>')

CONSENT = CONSENT.replace("__TAPE_JSON__", TAPE_JSON)


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
<link rel="stylesheet" href="/assets/site.css?v=5">
{ld_block}
</head><body><a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<header class="bar"><a href="/" class="wordmark" aria-label="Garbatrage — home"><img class="mark" src="/assets/logo-g-vector.svg" alt="G" width="24" height="28">Garbatrage</a><nav class="back"><a href="/markets/">Index</a> · <a href="/desk/">The Desk</a> · <a href="/archive/">Archive</a></nav></header>
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
    bav = (f'<span class="av">{esc(s.get("av") or av(s["author"]))}</span>'
           if not s.get("column") else "")  # column: speaker byline, no avatar
    # text-only TRUE FIGURE card (no image): a big figure with nothing behind it.
    fig_card = (f'<div class="figcard"><span class="figtag">TRUE FIGURE</span>'
                f'<div class="fignum">{esc(s.get("figure",""))}</div>'
                f'<div class="figcap">{esc(s.get("figcap","The number, with nothing behind it."))}</div></div>'
                if s.get("text_only") else
                f'<figure class="artbox"><img class="art-img" src="{art}" alt="" loading="lazy"></figure>')
    share = (f'<div class="share"><a href="https://twitter.com/intent/tweet?text={quote(s["title"])}&url={quote(url)}" target="_blank" rel="noopener">Post to X</a>'
             f'<a href="https://warpcast.com/~/compose?text={quote(s["title"])}&embeds[]={quote(url)}" target="_blank" rel="noopener">Cast</a>'
             f'<a href="{esc(url)}" data-copy>Copy link</a></div>')
    # E-01/E-02 house signature: wire pieces close with "Pays: X." The closer
    # is the last line that names who eats it — the thing that makes the site
    # recognisable. Columns carry their own-voice closer (E-waiver) so they
    # never get a Pays line bolted on.
    closer_sig = (''
        if s.get("column")
        else f'<p class="closer">{esc(s.get("closer", ""))}</p>')
    jsonld = {
        "type": "NewsArticle",
        "name": s["title"],
        "block": ('<script type="application/ld+json">'                  + json.dumps({
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
<p class="lede">{esc(s["dek"])}</p>{fig_card}
<div class="byline">{bav}<span><b>{esc(s["author"])}</b><br>{esc(s.get("role", ""))}</span>
<span class="rd"><time datetime="{esc(s["date"])}">{esc(s["date"])}</time> · {s.get("read", 4)} min read</span></div>
<article class="art">{s["body"]}</article>
{closer_sig}
<div class="tags">{"".join(f'<a class="chip" href="/tag/{esc(t)}/">{esc(t)}</a>' for t in s.get("tags", []) if isinstance(t, str))}</div>
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
def build_dump():
    """Render /dump/ — The Morning Dump. Reads data/dump.json (written by
    build_dump.py, which does the network fetch). The daily build itself never
    touches the network; if dump.json is absent/stale the page still renders
    with a deadpan fallback instead of breaking the deploy."""
    try:
        dump = json.loads((ROOT / "data" / "dump.json").read_text())
        videos = dump.get("videos") or []
    except Exception:
        videos = []
    if not videos:
        body = (f'<div class="kick">The Morning Dump</div>'
                f'<h1>Nothing is here yet.</h1>'
                f'<p class="lede">The dump is empty, which is the most '
                f'honest thing it has ever been.</p>')
        write("dump/index.html",
              layout("The Morning Dump · Garbatrage",
                     "A deadpan aggregate of the internet\u2019s funniest uploads.",
                     body, f"{SITE}/dump/"))
        return
    # Round-robin across channels so the grid is a true aggregate instead of
    # a high-volume-channel flood: take each channel's freshest, then next, etc.,
    # until 48 cards (or the pool exhausts). Keeps every channel represented.
    by_chan = {}
    for v in videos:
        by_chan.setdefault(v["channel"], []).append(v)
    for k in by_chan:
        by_chan[k].sort(key=lambda v: v["published"], reverse=True)
    picks = []
    idx = 0
    while len(picks) < 48 and any(by_chan[k] for k in by_chan):
        got = 0
        for k in list(by_chan):
            if by_chan[k]:
                picks.append(by_chan[k].pop(0)); got += 1
        if got == 0:
            break
        idx += 1
    card = ""
    for v in picks:
        card += (f'<div class="dump-card">'
                 f'<a class="dthumb" href="{esc(v["href"])}" target="_blank" '
                 f'rel="noopener" data-video="{esc(v["id"])}">'
                 f'<img src="{esc(v["thumb"])}" alt="" loading="eager">'
                 f'<span class="dplay">▶</span></a>'
                 f'<div class="dbody"><div class="dchan">{esc(v["channel"])}</div>'
                 f'<h3><a href="{esc(v["href"])}" target="_blank" rel="noopener">{esc(v["title"])}</a></h3></div>'
                 f'</div>')
    head = (f'<div class="kick dumpkick">The Morning Dump</div>'
            f'<h1 class="dumpt">The funniest uploads, for the most important moments of your day.</h1>')
    body = (head + f'<div class="dump-grid">{card}</div>'
            + ('<div class="disc">The Morning Dump curates uploads from The Onion, '
               'The Babylon Bee, The Daily Show, Last Week Tonight, Saturday Night Live, '
               'Key &amp; Peele, Dropout, Hard Times and Tim Dillon via their public feeds. '
               'It is an aggregate of other people\u2019s '
               'work, reported straight, and not investment advice.</div>')
            + ('<script data-cfasync="false">'
               '(function(){var c=\'https://www.youtube-nocookie.com/embed/\';'
               'document.querySelectorAll(\'.dthumb\').forEach(function(a){'
               'a.addEventListener(\'click\',function(e){e.preventDefault();var id=a.getAttribute(\'data-video\');'
               'a.innerHTML=\'<div class="dumpgrid-embed"><iframe src="\'+c+id+\'?autoplay=1" '
               'title="video" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
               'allowfullscreen></iframe></div>\';});});})();</script>'))
    write("dump/index.html",
          layout("The Morning Dump · Garbatrage",
                 "A deadpan aggregate of the internet\u2019s funniest uploads.",
                 body, f"{SITE}/dump/"))
    print(f"built /dump/ with {len(picks)} videos from {len(by_chan)} channels")


def build_feeds():
    urls = [f"{SITE}/", f"{SITE}/markets/", f"{SITE}/archive/", f"{SITE}/desk/", f"{SITE}/about/",
            f"{SITE}/methodology/", f"{SITE}/terms.html", f"{SITE}/privacy.html", f"{SITE}/list/"]
    urls += [f"{SITE}/tag/{t}/" for t in TAGS]
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
All quotes, indexes, tickers and figures are fabricated; any resemblance to real securities, people or firms is coincidental, or deliberate.
Nothing herein is investment, legal or tax advice. © Garbatrage Media Group LLC. Not a registered investment adviser.
Garbatrage Media Group LLC · <a href="mailto:info@garbatrage.com">info@garbatrage.com</a></div></footer>
<script data-cfasync="false">document.querySelectorAll('[data-copy]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();navigator.clipboard.writeText(a.href).then(function(){a.textContent='Copied';});});});</script>"""

def build_home():
    # Home shows the NEWEST six stories (lead + 5 briefs), by index, no bleed.
    lead = stories[0]
    lbav = (f'<span class="av">{esc(lead.get("av") or av(lead["author"]))}</span>'
            if not lead.get("column") else "")  # column lead: no avatar
    briefs = stories[1:6]
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
    # The List panel: header, GIA aggregate line, five movers (reasoned), disclaimer.
    try:
        _lst = json.loads((ROOT / "data" / "list.json").read_text())
    except Exception:
        _lst = []
    _movers = [r for r in _lst if r.get("reason")]
    _lst_lines = ""
    for r in _movers[:5]:
        _up = (r.get("delta") or 0) > 0
        _lst_lines += (f'<a class="li-it" href="/list/#{esc(r["slug"])}">'
                       f'<span class="r">{r["rank"]:02}</span>'
                       f'<span class="nm">{esc(r["name"])}<span class="pct {"up" if _up else "dn"}">{r["pct"]:+.1f}%</span></span>'
                       f'<span class="why">{esc(r["reason"])}</span></a>')
    _net = sum(1 for r in _movers if (r.get("delta") or 0) > 0) > sum(1 for r in _movers if (r.get("delta") or 0) < 0)
    _agg_cls = "up" if _net else "dn"; _agg_arrow = "▲" if _net else "▼"; _agg_sign = "+" if _net else "−"
    list_panel = (f'<div class="panel list-panel">'
                  f'<div class="ph"><span>The List</span><span>LST</span></div>'
                  f'<div class="lsum"><span class="lab">GIA</span><span class="tot">38,221.07</span>'
                  f'<span class="ch {_agg_cls}">{_agg_arrow} 52.91 ({_agg_sign}0.14%)</span></div>'
                  f'{_lst_lines}'
                  f'<div class="disc">The List is fictional. The GIA is not a benchmark. Prices invented.</div>'
                  f'<a class="li-more" href="/list/">All 25 &rarr;</a>'
                  f'</div>')
    # "From the Dump" — a few of the funniest live uploads, surfaced on home.
    dump_strip = ""
    try:
        _d = json.loads((ROOT / "data" / "dump.json").read_text())
        _vids = (_d.get("videos") or [])[:4]
    except Exception:
        _vids = []
    if _vids:
        _cards = "".join(
            f'<a class="dmin" href="{esc(v["href"])}" target="_blank" rel="noopener" '
            f'data-video="{esc(v["id"])}"><img src="{esc(v["thumb"])}" alt="" loading="lazy">'
            f'<span><b>{esc(v["channel"])}</b>{esc(v["title"])}</span></a>'
            for v in _vids)
        dump_strip = (f'<div class="dump-wrap">'
                      f'<div class="sec">From the Dump</div>'
                      f'<div class="dump-mini">{_cards}</div>'
                      f'<a class="dump-more" href="/dump/">Open the Dump →</a>'
                      f'</div>')
    brief_html = "".join(
        f'<a class="item" href="/story/{s["slug"]}/"><div class="thumb"><img src="{img(s)}" alt="" loading="lazy"></div><div>'
        f'<h3>{esc(s["title"])}</h3><p>{esc(s["dek"])}</p>'
        f'<div class="meta">{esc(s["desk"])} · {esc(s["author"])}</div></div></a>'
        for s in briefs)
    body = f"""\
<div class="mast">
  <div><h1 class="mmm">Garbatrage</h1><p class="mtag">Markets · Money · Mischief</p></div>
  <div class="mdate">{datetime.fromisoformat(lead["date"]).strftime("%A, %B %-d, %Y")}</div>
</div>
<div class="home">
<div class="col">
  <div class="kick">{esc(lead["desk"])}</div>
  <h1><a href="/story/{lead["slug"]}/">{esc(lead["title"])}</a></h1>
  <p class="dek">{esc(lead["dek"])}</p>
  <a class="hero" href="/story/{lead["slug"]}/"><img src="{img(lead)}" alt="" loading="lazy"></a>
  <div class="by">{lbav}<span><b>{esc(lead["author"])}</b> · {esc(lead.get("role", ""))} · {lead.get("read", 4)} min read</span></div>
  <div class="sec">Markets Brief</div>
  {brief_html}
</div>
<aside class="rail">
  {quotes_html}
  {list_panel}
</aside>
</div>
<div class="news"><div class="nin">
  <div><h2>The Morning Dump</h2><p>The day\u2019s headlines and the funniest new uploads, all in one place \u2014 for the part of the morning you\u2019d rather not discuss.</p></div>
  <div class="subs">
    <h3>The Dump, by email.</h3>
    <form action="https://garbatrage-social.nolanfarrell.workers.dev/subscribe" method="post" data-subscribe>
      <input type="email" name="email" placeholder="you@example.com" required aria-label="Email address">
      <input type="text" name="company" aria-hidden="true" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" class="hp">
      <button type="submit">Get the Dump</button>
      <small class="submsg" aria-live="polite"></small>
    </form>
  </div>
</div></div>
{dump_strip}
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

## ---------- The List ----------
def build_list():
    """/list/ — The List page: all 25, ranked, each name an anchor target."""
    try:
        _lst = json.loads((ROOT / "data" / "list.json").read_text())
    except Exception:
        _lst = []
    rows = ""
    for r in _lst:
        _up = (r.get("delta") or 0) > 0
        _dn = (r.get("delta") or 0) < 0
        _chg = ""
        if _up: _chg = f'<b class="up">{r["pct"]:+.1f}%</b>'
        elif _dn: _chg = f'<b class="dn">{r["pct"]:+.1f}%</b>'
        _why = f'<p class="why">{esc(r["reason"])}</p>' if r.get("reason") else ""
        rows += (f'<div class="li-row" id="{esc(r["slug"])}">'
                 f'<span class="r">{r["rank"]:02}</span>'
                 f'<div><h3>{esc(r["name"])}</h3>{_why}</div>'
                 f'<span class="w">{esc(r["worth"])}</span>'
                 f'<span class="c">{_chg}</span></div>')
    body = (f'<div class="kick">The List</div><h1>The List.</h1>'
            f'<p class="lede">Twenty-five people, ranked by worth, in a market that does not exist. '
            f'Three to five move each day; the rest hold steady, the way money does.</p>'
            f'<div class="li-grid">{rows}</div>'
            f'<div class="disc">The List is fictional. The GIA is not a benchmark. Prices invented.</div>')
    write("list/index.html",
          layout("The List · Garbatrage", "Twenty-five people, ranked by worth, in a market that does not exist.",
                 body, f"{SITE}/list/"))
    print(f"built /list/ with {len(_lst)} entries")

## ---------- Tag pages ----------
# The whitelist drives which /tag/<slug>/ pages exist. Adding a tag to this
# array makes a page automatically. The count is the honest surface: it is
# the number of pieces filed under that tag (desk match OR explicit tag), so
# a mis-filed piece (a telecom buyout under `etfs`) shows up in the count.
TAGS = ["markets", "rates", "earnings", "estate", "hauling", "etfs",
        "credit", "consumer", "prices"]

def _tagged_stories(tag):
    """Pieces that belong to a tag: explicit tag match OR desk filing."""
    out = []
    for s in stories:
        if tag in (s.get("tags") or []):
            out.append(s)
        elif s.get("desk") == tag:
            out.append(s)
    # newest first, stable
    return sorted(out, key=lambda s: s["date"], reverse=True)

def build_tags():
    for tag in TAGS:
        members = _tagged_stories(tag)
        tiles = "".join(
            f'<a class="chip{" on" if tag == _t else ""}" href="/tag/{_t}/">{_t}</a>'
            for _t in TAGS)
        rows = "".join(
            f'<div class="entry"><div class="d">{day(s["date"])}</div>'
            f'<a href="/story/{s["slug"]}/"><h3>{esc(s["title"])}</h3>'
            f'<div class="m"><b>{esc(s["desk"])}</b> · {esc(s["author"])}</div></a></div>'
            for s in members)
        body = [
            f'<div class="kick">Tag</div><h1>{esc(tag)}</h1>'
            f'<p class="lede">{esc(tag)} · {len(members)} piece{"s" if len(members)!=1 else ""}</p>'
            f'<div class="chips">{tiles}</div>']
        if members:
            body.append(rows)
        else:
            body.append('<p class="lede">Nothing filed here yet.</p>')
        body.append(DISC_INDEX)
        write(f"tag/{tag}/index.html",
              layout(f"{tag} · Garbatrage",
                     f"Every {tag} piece — {len(members)} filed.",
                     "".join(body), f"{SITE}/tag/{tag}/"))
    print(f"built /tag/ pages for {len(TAGS)} tags")

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
build_dump()
build_list()
build_tags()
build_feeds()
shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
# media/ (story illustration PNGs) lives outside static/; carry it into the build so
# `rm -rf site && build` cannot silently drop the images.
if (ROOT / "media").exists():
    if (OUT / "media").exists():
        shutil.rmtree(OUT / "media")
    shutil.copytree(ROOT / "media", OUT / "media")
print(f"built {len(stories)} stories, {len(cons)} companies, {len(gia['sectors'])} sectors, media carried")