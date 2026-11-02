#!/usr/bin/env python3
"""Generate per-story static pages with their own OG/Twitter meta.

Run after updating index.html's ARTICLES + articles_current.json so every
shared link (/story/N-slug.html) previews with that article's own headline
instead of the site hero. Idempotent: overwrites story/<N>-<slug>.html.

The <style> block is read live from index.html so story pages stay in sync
with the site theme. Keep this in sync with the SOP: every content refresh
must write articles_current.json AND run this.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
DATA = os.path.join(HERE, "articles_current.json")
OUTDIR = os.path.join(HERE, "story")
os.makedirs(OUTDIR, exist_ok=True)

SITE = "https://garbatrage.com"


def slugify(t):
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", t.lower()))[:60]


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    arts = data["articles"]
    src = open(INDEX, encoding="utf-8").read()

    style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)

    extra_css = """
.story-main{max-width:760px;margin:0 auto;padding:44px 26px 20px}
.story-top{max-width:760px;margin:0 auto;padding:26px 26px 0;display:flex;justify-content:space-between;align-items:center;gap:14px}
.story-top .back{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);text-decoration:none;letter-spacing:1px;text-transform:uppercase}
.story-top .back:hover{color:var(--brand)}
.story-banner{display:flex;align-items:center;gap:10px;margin-bottom:30px}
.story-banner .gword{font-family:'Montserrat',sans-serif;font-size:20px;font-weight:900;letter-spacing:1.5px;color:var(--white)}
.story-banner .gword span{color:var(--brand)}
.story-banner .gtag{padding:3px 8px;background:var(--brand);color:#fff;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:1px}
.story-h1{font-family:'Libre Franklin',sans-serif;font-size:clamp(26px,4vw,40px);line-height:1.08;color:var(--white);margin:0 0 18px;text-transform:unset}
.story-main .a-dek{font-size:17px;line-height:1.6;color:var(--text);margin-bottom:24px}
.story-main .art{width:100%;height:auto;border:1px solid var(--line);border-radius:6px;margin:8px 0 26px;display:block}
.story-main .a-byline{padding-bottom:22px;border-bottom:1px solid var(--line);margin-bottom:26px}
.story-main p{font-size:15px;line-height:1.75;color:var(--text);margin-bottom:18px}
.story-main p.lead{font-size:16px;color:var(--white)}
.story-main blockquote{border-left:2px solid var(--brand);padding:4px 0 4px 18px;margin:22px 0;font-size:16px;line-height:1.6;font-style:italic;color:var(--text)}
.story-main .a-tags{display:flex;gap:8px;margin-top:26px;padding-top:22px;border-top:1px solid var(--line)}
.story-main .a-tags .chip{color:var(--muted)}
.story-back{margin:34px 0 8px;text-align:center}
.story-back a{color:var(--brand);text-decoration:none;font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:1px;text-transform:uppercase}
.story-back a:hover{text-decoration:underline}
"""

    for i, a in enumerate(arts):
        slug = slugify(a["title"])
        url = f"{SITE}/story/{i}-{slug}.html"
        img_abs = f"{SITE}/{a['image']}"
        img_rel = os.path.join("..", a["image"])
        esc = html.escape
        chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in a["tags"])
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(a['title'])} · Garbatrage</title>
<meta name="description" content="{esc(a['dek'])}"/>
<meta property="og:site_name" content="Garbatrage"/>
<meta property="og:type" content="article"/>
<meta property="og:title" content="{esc(a['title'])}"/>
<meta property="og:description" content="{esc(a['dek'])}"/>
<meta property="og:image" content="{img_abs}"/>
<meta property="og:url" content="{url}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{esc(a['title'])}"/>
<meta name="twitter:description" content="{esc(a['dek'])}"/>
<meta name="twitter:image" content="{img_abs}"/>
<link rel="canonical" href="{url}"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;500;600;700;900&family=Inter:wght@400;500;600;700;900&family=JetBrains+Mono:wght@400;600;700&family=Montserrat:wght@900&display=swap" rel="stylesheet">
<style>
{style}
{extra_css}
</style>
</head>
<body style="background:var(--bg)">
<div class="story-top">
  <div style="display:flex;align-items:center;gap:12px">
    <svg width="30" height="30" viewBox="0 0 40 40" aria-label="Garbatrage mark"><rect x="1" y="1" width="38" height="38" rx="9" fill="#c83e3e"/><text x="20" y="33" text-anchor="middle" font-family="Montserrat, sans-serif" font-size="37" font-weight="900" fill="#ffffff">G</text></svg>
    <span class="story-banner"><span class="gword"><span>G</span>ARBATRAGE</span></span>
  </div>
  <a class="back" href="{SITE}/">← The Desk</a>
</div>
<main class="story-main">
  <div class="a-cat">{esc(a['cat'])}</div>
  <h1 class="story-h1">{a['title']}</h1>
  <div class="a-dek">{a['dek']}</div>
  <div class="a-byline">
    <div class="a-av">{esc(a['av'])}</div>
    <div><div class="a-name">{esc(a['name'])}</div><div class="a-role">{esc(a['role'])}</div></div>
  </div>
  <img class="art" src="{img_rel}" alt=""/>
  <div>{a['body']}</div>
  <div class="a-tags">{chips}</div>
  <div class="story-back">— <a href="{SITE}/">Read the full desk at Garbatrage</a> —</div>
</main>
<footer style="padding:30px 26px;border-top:2px solid var(--brand);background:var(--panel)">
  <div class="foot-dis" style="max-width:760px;margin:0 auto;font-size:11px;color:var(--faint);line-height:1.7;font-family:'JetBrains Mono',monospace">GARBATRAGE is a satirical publication, presented in the style of a professional financial news desk. All quotes, indexes, tickers and figures are fabricated. Nothing herein is investment, legal or tax advice.</div>
  <div class="copyright" style="text-align:center;color:var(--faint);font-size:11px;margin-top:18px;font-family:'JetBrains Mono',monospace">© Garbatrage Media Group LLC · For entertainment purposes only</div>
</footer>
</body>
</html>"""
        out = os.path.join(OUTDIR, f"{i}-{slug}.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"wrote {os.path.relpath(out, HERE)}")


if __name__ == "__main__":
    main()
