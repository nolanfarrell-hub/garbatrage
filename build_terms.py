#!/usr/bin/env python3
"""Generate the garbatrage.com legal pages (Terms + Privacy).

Reads the live <style> + fonts link from index.html so pages stay in sync
with the site theme. Idempotent: overwrites the target page.
"""
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")

src = open(INDEX, encoding="utf-8").read()
style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
fonts = re.search(r'<link href="https://fonts.googleapis.com/css2[^>]*>', src).group(0)

legal_css = """
/* ===== LEGAL PAGE ===== */
.legal-top{display:flex;justify-content:space-between;align-items:center;padding:14px 26px;border-bottom:1px solid var(--line);background:var(--bg)}
.legal-logo{display:flex;align-items:center;gap:10px}
.legal-logo a{font-family:'Montserrat',sans-serif;font-size:22px;font-weight:900;letter-spacing:1.5px;color:var(--white);text-decoration:none;display:flex;align-items:center;gap:8px}
.legal-logo i{font-style:normal;color:var(--brand)}
.legal-bar{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px}
.wrap{max-width:820px;margin:0 auto;padding:52px 26px 20px}
.kicker{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--brand);letter-spacing:2px;text-transform:uppercase}
.wrap h1{font-family:'Libre Franklin',sans-serif;font-weight:900;font-size:clamp(30px,5vw,46px);color:var(--white);margin:10px 0 22px;line-height:1.05}
.wrap h2{font-family:'Libre Franklin',sans-serif;font-weight:700;font-size:20px;color:var(--white);margin:34px 0 10px}
.wrap p{font-size:15px;line-height:1.75;color:var(--text);margin-bottom:16px}
.wrap p.caps{text-transform:uppercase;letter-spacing:.3px;font-size:13px;color:var(--muted);border-left:2px solid var(--brand);padding-left:16px}
.wrap ul{list-style:none;padding:0;margin:4px 0 16px}
.wrap ul li{position:relative;padding:5px 0 5px 20px;font-size:15px;line-height:1.7;color:var(--text)}
.wrap ul li:before{content:"";position:absolute;left:2px;top:14px;width:6px;height:6px;background:var(--brand)}
.wrap a{color:var(--brand);text-decoration:none}
.wrap a:hover{text-decoration:underline}
.wrap table{width:100%;border-collapse:collapse;margin:10px 0 18px;font-size:13px}
.wrap th{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);text-align:left;padding:9px 10px;border-bottom:2px solid var(--brand)}
.wrap td{padding:9px 10px;color:var(--text);line-height:1.5;border-bottom:1px solid var(--line);vertical-align:top}
.joke{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand);padding:18px 20px;font-size:14px;line-height:1.7;color:var(--text);border-radius:6px;margin-bottom:34px}
.joke strong{color:var(--white)}
.lede-joke{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand);padding:18px 20px;font-size:15px;line-height:1.7;color:var(--text);border-radius:6px;margin-bottom:30px}
.pull{border-left:2px solid var(--brand);padding:4px 0 4px 16px;margin:22px 0;font-size:16px;line-height:1.6;color:var(--white);font-style:italic}
/* ===== INDEX (GIA) PAGE ===== */
.gia-head{display:flex;justify-content:space-between;align-items:center;gap:20px;background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand);border-radius:8px;padding:22px 24px;margin:6px 0 10px;flex-wrap:wrap}
.gia-meta{display:flex;align-items:center;gap:16px}
.gia-symbol{font-family:'Montserrat',sans-serif;font-weight:900;font-size:26px;color:var(--brand);letter-spacing:1px}
.gia-name{font-family:'Libre Franklin',sans-serif;font-weight:700;font-size:19px;color:var(--white)}
.gia-level{text-align:right}
.gia-base{font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:600;color:var(--white)}
.gia-sub{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);margin-top:4px}
.sect-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.sector-chip{padding:5px 12px;border:1px solid var(--line);border-radius:30px;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);background:var(--panel)}
.table-scroll{overflow-x:auto;margin-top:6px}
.gia-table{width:100%;border-collapse:collapse;font-size:13px;min-width:860px}
.gia-table th{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);text-align:left;padding:10px 12px;border-bottom:2px solid var(--brand);position:sticky;top:0;background:var(--bg)}
.gia-table td{padding:14px 12px;border-bottom:1px solid var(--line);color:var(--text);vertical-align:top;line-height:1.5}
.gia-table .tick{font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--brand);white-space:nowrap}
.gia-table .co{min-width:260px}
.gia-table .co-n{font-weight:700;color:var(--white);font-size:14px}
.gia-table .co-b{font-size:12px;color:var(--muted);margin-top:3px}
.gia-table .co-f{display:flex;flex-direction:column;gap:3px;margin-top:7px;padding-top:7px;border-top:1px dashed var(--line)}
.gia-table .co-f .filing{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--brand-dim);letter-spacing:.3px}
.gia-table .co-f .quote{font-size:11px;color:var(--faint);font-style:italic}
.gia-table .cap{font-family:'JetBrains Mono',monospace;white-space:nowrap;color:var(--white)}
.gia-table .sec,.gia-table .ceo,.gia-table .fnd,.gia-table .hq{white-space:nowrap;font-size:12px;color:var(--muted)}
.legal-footer{border-top:2px solid var(--brand);padding:40px 26px;background:var(--panel)}
.legal-footlink{max-width:820px;margin:0 auto;display:flex;gap:22px;flex-wrap:wrap;align-items:center}
.legal-footlink a{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);text-decoration:none;text-transform:uppercase;letter-spacing:1px}
.legal-footlink a:hover{color:var(--brand)}
.legal-footlink span{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--faint)}
@media(max-width:700px){.legal-bar,.utc{display:none}.legal-top{flex-wrap:wrap;gap:10px}.wrap{padding-top:32px}.legal-footlink span{margin-left:0;width:100%;margin-top:14px}.wrap table{font-size:12px}.wrap th,.wrap td{padding:7px 6px}}
"""

nav_html = """
<div class="legal-top">
  <div class="legal-logo"><a class="brand" href="/" aria-label="Garbatrage, home">
<img class="mark" src="/assets/logo-cream.png" alt="" width="40" height="40">
<span class="word"><i>G</i>ARBATRAGE</span>
<span class="satire">Satire</span>
</a></div>
  <div class="nav" style="gap:18px">
    <a href="/#markets">Markets</a><a href="/#stories">Stories</a><a href="/#desk">The Desk</a><a href="/#community">Community</a>
  </div>
  <div class="utc">Legal</div>
</div>
"""

PAGES = [
    {
        "out": "terms.html",
        "title": "Terms of Service",
        "og_title": "Terms of Service · Garbatrage",
        "og_desc": "Read it, don't act on it, don't sue us.",
        "body": "terms_body.html",
    },
    {
        "out": "privacy.html",
        "title": "Privacy Policy",
        "og_title": "Privacy Policy · Garbatrage",
        "og_desc": "We barely know anything about you, and what we know we don't want.",
        "body": "privacy_body.html",
    },
    {
        "out": "indexes.html",
        "title": "Garbatrage Industrial Average",
        "og_title": "Garbatrage Industrial Average · Index Composition",
        "og_desc": "The full GIA roster: 25 hand-picked mid-value securities, rebalanced when someone remembers.",
        "body": "indexes_body.html",
        "banner": "Index Composition · As Of 5 November 2026",
    },
    {
        "out": "about.html",
        "title": "About",
        "og_title": "About · Garbatrage",
        "og_desc": "Garbatrage is a satirical financial publication. That is the whole answer.",
        "body": "about_body.html",
    },
    {
        "out": "methodology.html",
        "title": "Methodology",
        "og_title": "Methodology · Garbatrage",
        "og_desc": "How the index is built, and how the stories are made.",
        "body": "methodology_body.html",
    },
]

for p in PAGES:
    body = open(os.path.join(HERE, p["body"]), encoding="utf-8").read()
    if p["out"] == "indexes.html":
        data = json.load(open(os.path.join(HERE, "datasets/gia.json"), encoding="utf-8"))
        body = body.replace("__GIADATA__", json.dumps(data, ensure_ascii=False))
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{p["title"]} · Garbatrage</title>
<meta name="description" content="{p["og_desc"]}"/>
<meta property="og:site_name" content="Garbatrage"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{p["og_title"]}"/>
<meta property="og:description" content="{p["og_desc"]}"/>
<meta property="og:url" content="https://garbatrage.com/{p["out"]}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{p["og_title"]}"/>
<meta name="twitter:description" content="{p["og_desc"]}"/>

{fonts}
<style>
{style}
{legal_css}
</style>
</head>
<body>
{nav_html}
{body}
</body>
</html>
"""
    out = os.path.join(HERE, p["out"])
    open(out, "w", encoding="utf-8").write(page)
    print("wrote", out, len(page), "bytes")
