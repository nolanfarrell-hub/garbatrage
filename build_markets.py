#!/usr/bin/env python3
"""Generate the GIA markets index: /markets/ (all) + one sector-filtered page each.

Reads gia.json (prices build-owned), groups constituents by sector, renders the
chip rail (\"All\" + 10 sectors) with the active sector highlighted, and per-row
price/change. Every chip resolves to a real page; nothing is a dead link.
Rerun-safe: overwrites all pages.
"""
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
DATA = os.path.join(HERE, "datasets", "gia.json")
OUT = os.path.join(HERE, "markets")

src = open(INDEX, encoding="utf-8").read()
style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
fonts = re.search(r'<link href="https://fonts.googleapis.com/css2[^>]*>', src).group(0)
data = json.load(open(DATA, encoding="utf-8"))
cons = data["constituents"]
sectors = data["sectors"]

markets_css = """
/* ===== MARKETS (GIA index + sector filters) ===== */
.m-bar{display:flex;justify-content:space-between;align-items:center;padding:14px 26px;border-bottom:1px solid var(--line);background:var(--bg)}
.m-bar .brand{display:flex;align-items:center;gap:9px;text-decoration:none;color:inherit}
.m-bar .brand .mark{width:34px;height:34px;object-fit:contain;mix-blend-mode:screen}
.m-bar .brand .word{font-family:'Montserrat',sans-serif;font-size:22px;font-weight:900;letter-spacing:1.5px;color:var(--white)}
.m-bar .brand .word i{font-style:normal;color:var(--brand)}
.m-back{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);text-decoration:none;letter-spacing:1px;text-transform:uppercase}
.m-back:hover{color:var(--brand)}
.m-tape{display:flex;gap:26px;padding:9px 26px;border-bottom:1px solid var(--line);background:var(--panel);font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);overflow-x:auto}
.m-tape i{font-style:normal}
.m-tape .s{color:var(--brand);font-weight:700}
.m-tape .dn{color:var(--down)}
.m-tape .up{color:var(--up)}
.m-wrap{max-width:1000px;margin:0 auto;padding:40px 26px 20px}
.kick{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--brand);letter-spacing:2px;text-transform:uppercase}
.m-wrap h1{font-family:'Libre Franklin',sans-serif;font-weight:900;font-size:clamp(28px,4.6vw,42px);color:var(--white);margin:8px 0 6px;line-height:1.05}
.m-wrap .lede{font-size:16px;line-height:1.65;color:var(--text);margin:0 0 20px}
.summary{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand);border-radius:8px;padding:18px 22px;margin:4px 0 18px}
.summary b{font-family:'JetBrains Mono',monospace;font-size:28px;color:var(--white);font-weight:700}
.summary .ch{font-family:'JetBrains Mono',monospace;font-size:15px}
.summary .ch.dn{color:var(--down)}
.summary .ch.up{color:var(--up)}
.summary .n{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);width:100%}
.summary .f{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:var(--brand);border:1px solid var(--brand);padding:2px 9px;border-radius:3px;margin-left:auto;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips a{padding:5px 13px;border:1px solid var(--line);border-radius:30px;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);background:var(--panel);text-decoration:none}
.chips a:hover{border-color:var(--brand);color:var(--white)}
.chips a.on{background:var(--brand);border-color:var(--brand);color:#fff}
.m-wrap h2{font-family:'Libre Franklin',sans-serif;font-weight:700;font-size:20px;color:var(--white);margin:34px 0 6px;display:flex;align-items:baseline;gap:10px}
.m-wrap h2 span{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--faint);font-weight:400;letter-spacing:1px;text-transform:uppercase}
.m-wrap table{width:100%;border-collapse:collapse}
.m-wrap tr{border-bottom:1px solid var(--line)}
.m-wrap td{padding:12px 12px;color:var(--text);font-size:14px;vertical-align:middle}
.m-wrap td.t{font-family:'JetBrains Mono',monospace;color:var(--brand);font-weight:700;width:70px}
.m-wrap td.nm a{color:var(--white);text-decoration:none}
.m-wrap td.nm a:hover{color:var(--brand)}
.m-wrap td.cap{color:var(--muted);width:100px}
.m-wrap td.px{font-family:'JetBrains Mono',monospace;color:var(--white);width:90px;text-align:right}
.m-wrap td.ch.up{color:var(--up);font-family:'JetBrains Mono',monospace;width:70px;text-align:right}
.m-wrap td.ch.dn{color:var(--down);font-family:'JetBrains Mono',monospace;width:70px;text-align:right}
.disc{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand);border-radius:6px;padding:16px 18px;font-size:13px;line-height:1.7;color:var(--muted);margin:34px 0 6px}
@media(max-width:700px){.m-tape span:nth-child(n+4){display:none}.m-wrap td.cap{display:none}}
"""

def slug(t): return t.lower().replace(" ","-")

def fmt_price(p):
    try: v=float(p)
    except (TypeError,ValueError): return p
    if v>=1000: return "{:,}".format(int(round(v)))
    return "$%.2f" % v

def chclass(c):
    return "up" if c>=0 else "dn"
def chsign(c):
    return "+" if c>0 else ""

def tape():
    t = '<span><i class="s">GIA</i> 38,221.07 <i class="dn">-0.83%</i></span>'
    for tk in ["TRSH","BYTBN","MJNK"]:
        c=next(x for x in cons if x["ticker"]==tk)
        cc=c["change"]
        t+=f'<span><i class="s">{tk}</i> {fmt_price(c["price"])} <i class="{chclass(cc)}">{chsign(cc)}{abs(cc):.2f}%</i></span>'
    return t

def rows_for(group_cons):
    out=""
    for c in group_cons:
        cc=c["change"]
        out+=f'<tr><td class="t">{c["ticker"]}</td><td class="nm"><a href="/company/{slug(c["ticker"])}/">{c["name"]}</a></td><td class="cap">{c["cap"]}</td><td class="px">{fmt_price(c["price"])}</td><td class="ch {chclass(cc)}">{chsign(cc)}{abs(cc):.2f}%</td></tr>'
    return out

def chips(active):
    out=f'<a href="/markets/" class="{"on" if active=="All" else ""}">All</a>'
    for s in sectors:
        out+=f'<a href="/markets/{slug(s)}/" class="{"on" if active==s else ""}">{s}</a>'
    return out

def build(active="All"):
    is_all = active=="All"
    group = cons if is_all else [c for c in cons if c["sector"]==active]
    group_per_sector={}
    for c in cons:
        group_per_sector.setdefault(c["sector"],[]).append(c)
    # group by sector (only sectors present)
    body=""
    if is_all:
        sec_order=[]
        for c in cons:
            if c["sector"] not in sec_order: sec_order.append(c["sector"])
        for s in sec_order:
            sg=group_per_sector[s]
            body+=f'<h2>{s} <span>{len(sg)} of 25</span></h2><table><tbody>{rows_for(sg)}</tbody></table>'
    else:
        body=f'<h2>{active} <span>{len(group)} of 25</span></h2><table><tbody>{rows_for(group)}</tbody></table>'
    h1 = "The Garbatrage Industrial Average" if is_all else f"{active} · GIA Constituents"
    lede = ("Twenty-five constituents, hand-picked, weighted by price and by mood. Composition is discretionary. Rebalancing happens when someone remembers."
            if is_all else f"The {active} wing of the Garbatrage Industrial Average. {len(group)} hand-picked mid-value {'security' if len(group)==1 else 'securities'}.")
    kick = "Markets · Index Construction"
    summ_cls = "dn"
    disc = ("Every constituent is fictional. The GIA is a proprietary index of hand-picked mid-value securities, is not calculated by any exchange, and is not a real benchmark. Prices shown are invented. Nothing here is investment advice."
            if is_all else f"Every constituent is fictional. {active} companies on this page are invented members of the GIA, a proprietary index of hand-picked mid-value securities that is not a real benchmark. Prices shown are invented. Nothing here is investment advice.")
    # non-all pages also show the summary strip for context
    summary = '<div class="summary"><b>38,221.07</b><span class="ch dn">▼ 321.44 (-0.83%)</span><span class="f">Fictional</span><span class="n">Down on mixed hauling volumes</span></div>' if is_all else '<div class="summary"><b>38,221.07</b><span class="ch dn">▼ 321.44 (-0.83%)</span><span class="f">Fictional</span><span class="n">The index is fictional. So is the hauling.</span></div>'

    html=f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{h1} · Garbatrage</title>
<meta name="description" content="{h1}. A fictional index of twenty-five fictional companies."/>
<meta property="og:site_name" content="Garbatrage"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{h1} · Garbatrage"/>
<meta property="og:description" content="A fictional index of twenty-five hand-picked mid-value securities."/>
<meta property="og:url" content="https://garbatrage.com/markets/{'' if is_all else slug(active)+'/'}"/>
{fonts}
<style>
{style}
{markets_css}
</style>
</head>
<body>
<div class="m-bar">
  <a class="brand" href="/" aria-label="Garbatrage, home"><img class="mark" src="/assets/logo-cream.png" alt="" width="34" height="34"><span class="word"><i>G</i>ARBATRAGE</span></a>
  <a class="m-back" href="/markets/"><span>← </span>All constituents</a>
</div>
<div class="m-tape">{tape()}</div>

<div class="m-wrap">
  <div class="kick">{kick}</div>
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
  {summary}
  <div class="chips">{chips(active)}</div>
  {body}
  <div class="disc">{disc}</div>
</div>
</body>
</html>
"""
    return html

os.makedirs(OUT, exist_ok=True)
# All page
open(os.path.join(OUT,"index.html"),"w",encoding="utf-8").write(build("All"))
print("wrote /markets/index.html")
# sector pages
for s in sectors:
    g=[c for c in cons if c["sector"]==s]
    sd=os.path.join(OUT,slug(s))
    os.makedirs(sd, exist_ok=True)
    open(os.path.join(sd,"index.html"),"w",encoding="utf-8").write(build(s))
    print("wrote /markets/"+slug(s)+"/  ("+str(len(g))+" cons)")
print("done")
