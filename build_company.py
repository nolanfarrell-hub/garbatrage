#!/usr/bin/env python3
"""Generate /company/{slug}/index.html for each GIA constituent.

Reads gia.json (prices live there, generated not hand-written), reuses the
index theme, and writes one self-contained page per constituent with:
  - per-constituent price/change from the dataset
  - stats table (ticker, sector, cap, ceo, founded, hq, index weight)
  - business body, quote, recent filings
  - mandatory fictional disclaimer IN A BOX, above the pager, in the reading path
  - prev/next pager clamped at the ends ("Constituent N of 25")
  - back link to the full roster
Rerun-safe: overwrites all company pages.
"""
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
DATA = os.path.join(HERE, "datasets", "gia.json")
OUTDIR = os.path.join(HERE, "company")

src = open(INDEX, encoding="utf-8").read()
style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
fonts = re.search(r'<link href="https://fonts.googleapis.com/css2[^>]*>', src).group(0)
data = json.load(open(DATA, encoding="utf-8"))
cons = data["constituents"]

company_css = """
/* ===== COMPANY PAGE ===== */
.c-bar{display:flex;justify-content:space-between;align-items:center;padding:14px 26px;border-bottom:1px solid var(--line);background:var(--bg)}
.c-bar .brand{display:flex;align-items:center;gap:9px;text-decoration:none;color:inherit}
.c-bar .brand .mark{width:34px;height:34px;object-fit:contain;mix-blend-mode:screen}
.c-bar .brand .word{font-family:'Montserrat',sans-serif;font-size:22px;font-weight:900;letter-spacing:1.5px;color:var(--white)}
.c-bar .brand .word i{font-style:normal;color:var(--brand)}
.c-back{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);text-decoration:none;letter-spacing:1px;text-transform:uppercase}
.c-back:hover{color:var(--brand)}
.c-tape{display:flex;gap:26px;padding:9px 26px;border-bottom:1px solid var(--line);background:var(--panel);font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);overflow-x:auto}
.c-tape i{font-style:normal}
.c-tape .s{color:var(--brand);font-weight:700}
.c-tape .dn{color:var(--down)}
.c-tape .up{color:var(--up)}
.c-wrap{max-width:820px;margin:0 auto;padding:40px 26px 20px}
.kick{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--brand);letter-spacing:2px;text-transform:uppercase}
.c-wrap h1{font-family:'Libre Franklin',sans-serif;font-weight:900;font-size:clamp(30px,5vw,46px);color:var(--white);margin:8px 0 6px;line-height:1.05}
.price{display:flex;align-items:baseline;gap:14px;font-family:'JetBrains Mono',monospace;margin:4px 0 18px}
.price b{font-size:30px;color:var(--white);font-weight:700}
.price .ch{font-size:16px;font-weight:600}
.price .ch.up{color:var(--up)}
.price .ch.dn{color:var(--down)}
.price .tick{font-size:13px;color:var(--muted);border:1px solid var(--line);padding:1px 7px;border-radius:3px}
.c-wrap .lede{font-size:17px;line-height:1.65;color:var(--text);margin:6px 0 22px}
.c-wrap h2{font-family:'Libre Franklin',sans-serif;font-weight:700;font-size:20px;color:var(--white);margin:30px 0 10px}
.c-wrap p{font-size:15px;line-height:1.75;color:var(--text);margin-bottom:16px}
.c-wrap table{width:100%;border-collapse:collapse;font-size:14px;margin:6px 0 8px}
.c-wrap th{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);text-align:left;padding:9px 10px;border-bottom:2px solid var(--brand);width:42%}
.c-wrap td{padding:9px 10px;color:var(--text);border-bottom:1px solid var(--line);vertical-align:top}
.quote{border-left:2px solid var(--brand);padding:4px 0 4px 18px;margin:22px 0;font-size:16px;line-height:1.6;color:var(--white);font-style:italic}
.quote i{display:block;font-family:'JetBrains Mono',monospace;font-size:11px;font-style:normal;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-top:10px}
ul.fil{list-style:none;padding:0}
ul.fil li{padding:12px 0 12px 2px;border-bottom:1px solid var(--line);font-size:14px;line-height:1.6;color:var(--text)}
ul.fil li span{display:block;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--brand);letter-spacing:1px;text-transform:uppercase;margin-bottom:3px}
.rel{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:8px 0}
.rel a{display:block;background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px;text-decoration:none}
.rel a:hover{border-color:var(--brand)}
.rel h3{font-family:'Libre Franklin',sans-serif;font-size:15px;font-weight:700;color:var(--white);line-height:1.35;margin:0 0 8px}
.rel .m{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.disc{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand);border-radius:6px;padding:16px 18px;font-size:13px;line-height:1.7;color:var(--muted);margin:34px 0 18px}
.disc b{color:var(--white)}
.pager{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);padding-top:16px;font-family:'JetBrains Mono',monospace;font-size:12px}
.pager a{color:var(--brand);text-decoration:none;text-transform:uppercase;letter-spacing:1px}
.pager a:hover{text-decoration:underline}
.pager span{color:var(--muted)}
@media(max-width:700px){.c-tape span:nth-child(n+3){display:none}.rel{grid-template-columns:1fr}.c-back span{display:none}}
"""

def slug(t): return t.lower()

def fmt_price(p):
    try:
        v=float(p)
    except (TypeError,ValueError):
        return p
    if v >= 1000:
        return "{:,}".format(int(round(v)))
    return "$%.2f" % v

def page_for(c, idx, prev, nxt):
    t=c["ticker"]
    nm=c["name"]
    p=fmt_price(c.get("price"))
    chg=c.get("change",0)
    chgcls="up" if chg>=0 else "dn"
    chsign="+" if chg>0 else ""
    # tape row
    tape = f'<span><i class="s">GIA</i> 38,221.07 <i class="dn">-0.83%</i></span>'
    tape += f'<span><i class="s">{t}</i> {p} <i class="{chgcls}">{chsign}{abs(chg):.2f}%</i></span>'
    # a couple peer rows in tape
    peers=[prev,nxt]
    for q in peers:
        if q:
            qp=fmt_price(q.get("price"))
            qc=q.get("change",0)
            qq="up" if qc>=0 else "dn"
            tape+=f'<span><i class="s">{q["ticker"]}</i> {qp} <i class="{qq}">{qc:+.2f}%</i></span>'
    # filings
    fil=""
    for f in c.get("filings",[]):
        fil+=f'<li><span>{f["type"]} · {f["when"]}</span>{f["text"]}</li>'
    # related (links to prev/next stories are placeholder; link to nearest stories)
    rel = f'<a href="/story/"><h3>Waste sector advances as second-quarter volumes exceed expectations</h3><div class="m">Markets · Marcus Reid</div></a>'
    rel += f'<a href="/story/"><h3>Collection rate expansion continues to outpace guidance</h3><div class="m">Hauling · Tessa Nguyen</div></a>'
    # prev/next
    prev_a = f'<a href="/company/{slug(prev["ticker"])}/">← {prev["ticker"]}</a>' if prev else '<span>← Home of the index</span>'
    nxt_a = f'<a href="/company/{slug(nxt["ticker"])}/">{nxt["ticker"]} →</a>' if nxt else '<span>End of the line →</span>'
    num = f'Constituent {idx+1} of 25'
    # sector + back
    lede = c.get("lede","")
    quote = c.get("quote","")
    bus = c.get("business","")
    sector=c.get("sector","")
    disc = f'<div class="disc"><b>{t} is a fictional security.</b> It is not listed on any exchange, is not held by any fund, and cannot be bought. The Garbatrage Industrial Average is a proprietary index of hand-picked mid-value securities and is not a real benchmark. Nothing here is investment advice.</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{nm} ({t}) · Garbatrage</title>
<meta name="description" content="{nm} — {sector} constituent of the Garbatrage Industrial Average. Fictional."/>
<meta property="og:site_name" content="Garbatrage"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{nm} ({t}) · Garbatrage"/>
<meta property="og:description" content="{nm} — {sector} constituent of the Garbatrage Industrial Average. Fictional."/>
<meta property="og:url" content="https://garbatrage.com/company/{slug(t)}/"/>
{fonts}
<style>
{style}
{company_css}
</style>
</head>
<body>
<div class="c-bar">
  <a class="brand" href="/" aria-label="Garbatrage, home"><img class="mark" src="/assets/logo-cream.png" alt="" width="34" height="34"><span class="word"><i>G</i>ARBATRAGE</span></a>
  <a class="c-back" href="/indexes.html"><span>← </span>All constituents</a>
</div>
<div class="c-tape">{tape}</div>

<div class="c-wrap">
  <div class="kick">{sector} · GIA Constituent</div>
  <h1>{nm}</h1>
  <div class="price"><b>{p}</b><span class="ch {chgcls}">{chsign}{abs(chg):.2f}%</span><span class="tick">{t}</span></div>

  <p class="lede">{lede}</p>

  <table>
  <tbody>
  <tr><th>Ticker</th><td>{t}</td></tr>
  <tr><th>Sector</th><td>{sector}</td></tr>
  <tr><th>Market cap</th><td>{c.get("cap","")}</td></tr>
  <tr><th>Chief executive</th><td>{c.get("ceo","")}</td></tr>
  <tr><th>Founded</th><td>{c.get("founded","")}</td></tr>
  <tr><th>Headquarters</th><td>{c.get("hq","")}</td></tr>
  <tr><th>Index weight</th><td>{c.get("weight",0)}%</td></tr>
  </tbody>
  </table>

  <h2>Business</h2>
  <p>{bus}</p>

  <div class="quote">“{quote}”<i>{c.get("ceo","")}</i></div>

  <h2>Recent filings</h2>
  <ul class="fil">{fil}</ul>

  <h2>Related</h2>
  <div class="rel">{rel}</div>

  {disc}
  <div class="pager">{prev_a}<span>{num}</span>{nxt_a}</div>
</div>
</body>
</html>
"""
    return html

os.makedirs(OUTDIR, exist_ok=True)
n=len(cons)
for i,c in enumerate(cons):
    prev=cons[i-1] if i>0 else None
    nxt=cons[i+1] if i<n-1 else None
    html=page_for(c,i,prev,nxt)
    out=os.path.join(OUTDIR, slug(c["ticker"]), "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out,"w",encoding="utf-8").write(html)
    print("wrote", out, len(html), "bytes")
print("done", n, "pages")
