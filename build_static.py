#!/usr/bin/env python3
"""Hand-author the static pages (terms/privacy/about/methodology) that build_site does not
emit. They must match build_site.layout()'s chrome exactly — same head, fonts, bar, tape —
so the whole site is consistent by construction. Run once; the output lives in static/.
"""
import html, os, json
ROOT=os.path.dirname(os.path.abspath(__file__))
STATIC=os.path.join(ROOT,"static")
SITE="https://garbatrage.com"

def esc(s): return html.escape(str(s), quote=True)

# Build the tape from the real gia data (matches build_site's TAPE)
gia=json.load(open(os.path.join(ROOT,"data","gia.json"),encoding="utf-8"))
cons=gia["constituents"]
TAPE="".join(
    f'<span><i class="s">{esc(c["ticker"])}</i> {c["price"]} '
    f'<i class="{"up" if c["change"] >= 0 else "dn"}">{c["change"]:+.1f}%</i></span>'
    for c in cons[:8])

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

LEGAL_STYLE = """
<style>
.legal{max-width:780px}
.legal h2{font-size:24px}
.legal p,.legal li{max-width:72ch}
.legal p{font-size:14px;line-height:1.8;margin-bottom:16px}
.legal ul{margin:0 0 18px 0;padding-left:20px}
.legal ul li{margin-bottom:8px;font-size:14px;line-height:1.7}
.legal table{font-size:13px}
.legal table td:first-child{font-weight:600;white-space:nowrap;width:200px}
.ching{margin:0 0 30px}
.chl{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--maroon);border-radius:6px;padding:16px 20px;font-size:14px;line-height:1.7;margin-bottom:24px}
.pull{border-left:3px solid var(--maroon);padding:4px 0 4px 20px;margin:24px 0;font-family:'Abril Fatface',serif;font-size:20px;line-height:1.45;color:var(--ink)}
.mt{color:var(--faint);font-size:11px;letter-spacing:1px;text-transform:uppercase;margin-top:34px}
</style>"""

def legal_body(*blocks):
    return LEGAL_STYLE + "\n".join(blocks)

# ---- Terms ----
terms=legal_body(
'<div class="kick">Legal · Terms</div>',
'<h1>Terms of Service</h1>',
'<p class="chl">The terms are: read it, don\'t act on it, don\'t sue us. You\'re a reasonable visitor visiting a joke. Act accordingly. — The parts below are the version a lawyer made us write, and they say the same thing at greater length.</p>',
'<div class="legal"><p>These Terms of Service ("Terms") are a binding agreement between you and <strong>Garbatrage Media Group LLC</strong> ("Garbatrage," "we," "us") covering your use of garbatrage.com and everything on it (the "Site"). By using the Site you accept these Terms. If you don\'t, stop using the Site.</p>',
'<h2>1. What this site is</h2><p>Garbatrage is a <strong>satirical publication</strong>. It is presented in the visual and typographic style of a professional financial news desk. Most of what you read here is invented.</p><p>Specifically:</p><ul><li>Headlines, articles, quotations, companies, indexes, anchors, tickers and figures are <strong>fabricated</strong> unless stated otherwise.</li><li>Any resemblance to real securities, firms, funds, people or events is coincidental, or deliberate, and in either case is not a representation of fact.</li><li>The <strong>Garbatrage Industrial Average ("GIA")</strong> is a fictional index. It is not a benchmark, is not calculated by any exchange, and is not licensed to anyone.</li><li>Where the Site displays <strong>real market prices</strong>, those prices are supplied by third parties (see §6) and may be delayed, incomplete, or wrong. Their presence does not make anything else on the Site factual.</li></ul>',
'<h2>2. Not advice</h2><p>Nothing on the Site is investment, financial, legal, tax or accounting advice, and nothing is a recommendation, offer or solicitation to buy or sell any security. We are not a registered investment adviser, broker-dealer, or exchange.</p><p>Do not rely on the Site to make a decision. If you do, and it goes badly, that is the normal outcome and not our fault. Consult a licensed professional.</p>',
'<h2>3. Use of the Site</h2><p>You may read, link to, and quote the Site for ordinary purposes, with attribution. You may not:</p><ul><li>Scrape or crawl at a volume that degrades service for others;</li><li>Republish substantial portions commercially without permission (see §7);</li><li>Present our satirical content as factual reporting, or as the work of another publication;</li><li>Interfere with, probe, or attempt to bypass security;</li><li>Use the Site in violation of law.</li></ul>',
'<h2>4. Third-party data and content</h2><p>Market data, charts, ticker tape and quote widgets are provided by third parties, including TradingView and Finnhub. Their data is subject to their own terms, and their attribution notices must not be removed. We do not control it, do not guarantee its accuracy, timeliness or availability, and are not responsible for it.</p>',
'<h2>5. No warranty</h2><p>The site is provided "as is" and "as available," without warranty of any kind, express or implied, including merchantability, fitness for a particular purpose, accuracy and non-infringement. We do not warrant that the site will be uninterrupted, secure, or error-free, or that any figure displayed is correct.</p>',
'<h2>6. Limitation of liability</h2><p>To the maximum extent permitted by law, Garbatrage and its members, officers and contributors shall not be liable for any indirect, incidental, special, consequential, exemplary or punitive damages, or for lost profits, lost data, or trading losses, arising out of or relating to your use of the site, whether based in contract, tort, or otherwise, even if advised of the possibility. Our total aggregate liability for all claims relating to the site shall not exceed one hundred U.S. dollars ($100).</p><p>Some jurisdictions don\'t allow certain exclusions, so parts of this may not apply to you.</p>',
'<h2>7. Our content</h2><p>The Site\'s name, logo, wordmark, layout, and written content are owned by Garbatrage Media Group LLC or used under license. All rights reserved.</p><p>Because a portion of our text is machine-assisted, some of it may not attract independent copyright protection in every jurisdiction. That does not affect our rights in the compilation, the branding, or the human-edited portions.</p><p><strong>Quoting:</strong> up to roughly 150 words, with a link and credit to Garbatrage, is fine and encouraged. For anything more, or for syndication or commercial reuse, ask: <a href="mailto:info@garbatrage.com">info@garbatrage.com</a>.</p>',
'<h2>8. Copyright complaints</h2><p>If you believe material on the Site infringes your copyright, send a notice to <a href="mailto:info@garbatrage.com">info@garbatrage.com</a> including: identification of the work, the URL of the allegedly infringing material, your contact details, a statement of good-faith belief, a statement under penalty of perjury that the information is accurate and you are authorised to act, and your physical or electronic signature.</p>',
'<h2>9. Email</h2><p>If you subscribe to any newsletter, you consent to receive it. Every send includes a one-click unsubscribe, and unsubscribing takes effect within ten business days at the outside. Our postal address appears in each send, as required.</p>',
'<h2>10. Changes</h2><p>We may change these Terms. The effective date at the top will change with them, and material changes will be noted on the Site. Continuing to use the Site after a change accepts it.</p>',
'<h2>11. Governing law and disputes</h2><p>These Terms are governed by the laws of the State of Colorado, without regard to conflict-of-law rules. Any dispute shall be brought in the state or federal courts located in Denver County, Colorado, and you consent to their jurisdiction.</p><p>To the extent permitted by law, you and Garbatrage each waive the right to a jury trial and the right to participate in a class action or class-wide arbitration.</p>',
'<h2>12. Severability and entire agreement</h2><p>If a provision is unenforceable, the rest survives. These Terms, with the Privacy Policy, are the entire agreement between us regarding the Site.</p>',
'<h2>13. Contact</h2><p>Garbatrage Media Group LLC · <a href="mailto:info@garbatrage.com">info@garbatrage.com</a></p></div>'
)
open(os.path.join(STATIC,"terms.html"),"w").write(
    layout("Terms of Service · Garbatrage","Read it, don't act on it, don't sue us.", terms, f"{SITE}/terms.html"))
print("wrote static/terms.html")

# ---- Privacy ----
privacy=legal_body(
'<div class="kick">Legal · Privacy</div>',
'<h1>Privacy Policy</h1>',
'<p class="chl">We barely know anything about you, and what we know we don\'t want. That\'s the policy, in full, forever. — The version below is longer because several of our suppliers insist on it.</p>',
'<div class="legal"><p>This policy explains what <strong>Garbatrage Media Group LLC</strong> ("we") collects when you visit garbatrage.com, why, and what you can do about it.</p>',
'<h2>1. Short version</h2><p>There are no accounts, no logins, and no first-party tracking cookies. We don\'t build profiles and we don\'t sell data. What exists is ordinary server logging plus a handful of third-party embeds that come with their own identifiers.</p>',
'<h2>2. What we collect</h2><table><tr><th>Category</th><th>Detail</th><th>Source</th></tr><tr><td>Server logs</td><td>IP address, user agent, referrer, requested URL, timestamp, country</td><td>Cloudflare</td></tr><tr><td>Aggregate analytics</td><td>Pageviews, country, referrer, device class — cookieless</td><td>Cloudflare Insights</td></tr><tr><td>Font requests</td><td>IP, user agent</td><td>Google Fonts</td></tr><tr><td>Market data requests</td><td>IP, user agent, requested symbols</td><td>Finnhub, TradingView</td></tr><tr><td>Email address</td><td>Only if you subscribe to the newsletter</td><td>You</td></tr></table><p>We do not knowingly collect special-category data, and we don\'t ask for your name.</p>',
'<h2>3. Why</h2><ul><li><strong>To serve the site</strong> — routing, caching, security, abuse prevention (legitimate interest).</li><li><strong>To count readers</strong> — aggregate, cookieless (legitimate interest).</li><li><strong>To send the newsletter</strong> — if and only if you asked (consent, and performance of our agreement with you).</li><li><strong>To fix things</strong> — diagnosing errors and load (legitimate interest).</li></ul>',
'<h2>4. Cookies</h2><p>We set no first-party cookies. Third-party embeds may set their own; TradingView in particular may. Where a non-essential third-party cookie is set and you are in the UK or EEA, consent is requested before it is used. You can block cookies in your browser without breaking the site, though some widgets may not load.</p>',
'<h2>5. Retention</h2><p>Server logs: 30 days. Aggregate analytics: 6 months. Newsletter address: until you unsubscribe, plus 30 days to honour the request.</p>',
'<h2>6. Sharing</h2><p>We share data with the processors listed in §2, and with our email provider if you subscribe. We do not sell personal information, and we do not share it for cross-context behavioural advertising. If that changes — for example if we take advertising — this section will change first, and before the change takes effect.</p>',
'<h2>7. Your rights (UK/EEA)</h2><p>You have the right to access, rectify, erase, restrict, port, and object to processing, and to withdraw consent. Write to <a href="mailto:info@garbatrage.com">info@garbatrage.com</a>. We respond within one month. You may also complain to your national supervisory authority.</p>',
'<h2>8. Your rights (California)</h2><p>Under the CCPA/CPRA you have the right to know what is collected, to delete it, to correct it, to opt out of sale or sharing, and to non-discrimination for exercising those rights. We do not currently sell or share personal information as those terms are defined. Requests: <a href="mailto:info@garbatrage.com">info@garbatrage.com</a>, subject line "CCPA."</p>',
'<h2>9. International transfers</h2><p>Our processors are mostly US-based, so data reaches the United States. Transfers rely on Standard Contractual Clauses or an adequacy decision where required.</p>',
'<h2>10. Security</h2><p>The site is served over TLS via Cloudflare. No system is perfect, and we hold very little worth stealing.</p>',
'<h2>11. Children</h2><p>The Site is not directed at children under 13, and we do not knowingly collect their data.</p>',
'<h2>12. Do Not Track</h2><p>Because we set no first-party tracking cookies, DNT is largely satisfied by default. We do not currently alter behaviour in response to the header.</p>',
'<h2>13. Changes</h2><p>Material changes will be posted here with a new effective date, and flagged on the Site for 30 days.</p>',
'<h2>14. Contact</h2><p>Garbatrage Media Group LLC · <a href="mailto:info@garbatrage.com">info@garbatrage.com</a></p></div>'
)
open(os.path.join(STATIC,"privacy.html"),"w").write(
    layout("Privacy Policy · Garbatrage","We barely know anything about you, and what we know we don't want.", privacy, f"{SITE}/privacy.html"))
print("wrote static/privacy.html")

# ---- About (becomes static/about/index.html) ----
about=legal_body(
'<div class="kick">Company · About</div>',
'<h1>About</h1>',
'<p class="chl">Garbatrage is a satirical financial publication. That is the whole answer, and we are aware we have now written it in several places. The rest of this page exists because people keep asking a second question, and the second question is usually "but which parts."</p>',
'<div class="legal"><h2>What this is</h2><p>A daily financial news desk, in the visual and typographic register of the real thing, reporting on a market that does not exist. We write about the Garbatrage Industrial Average and the twenty-five companies in it. We write about rate policy, fund structures, family offices and hauling volumes. We do it deadpan, on time, and without winking at the reader mid-sentence.</p><p>The register is the joke. Finance already talks like this. We mostly just refuse to stop.</p>',
'<h2>What is invented</h2><p>Everything, unless marked otherwise.</p><ul><li>Headlines, articles, quotes, sources, companies, indexes, tickers and figures are fabricated.</li><li>The anchors are fictional people with fictional beats.</li><li>Where real market prices appear — the tape at the top of the page — those are real, supplied by third parties, and can be delayed or wrong.</li><li>Any resemblance to real firms or people is either coincidence or deliberate, and is not a factual claim either way.</li></ul>',
'<div class="pull">Nothing here is investment advice. We are not a registered adviser, a broker, or an exchange. Do not act on it. See the <a href="/terms.html">Terms</a>.</div>',
'<h2>Who makes it</h2><p>Garbatrage is written and edited by a small desk, and is machine-assisted. A human writes and edits every published piece; machine tooling is used for drafting, art and production. We say so plainly because a lot of sites don\'t.</p><p>The bylines are fictional. The desk behind them is not.</p>',
'<h2>Corrections</h2><p>We correct errors in the fiction — a ticker that contradicts an earlier one, a company with two founding dates, an anchor who dies and then files. Corrections are appended to the piece, not silently made. Send them to <a href="mailto:info@garbatrage.com">info@garbatrage.com</a> with the URL.</p><p>We do not correct the satire. If the joke is wrong, that\'s a different department.</p>',
'<h2>Ownership and funding</h2><p>Independently owned by Garbatrage Media Group LLC. No outside investment, no parent company, no sponsor yet.</p><p>When there is sponsored content, it will carry a label at the top of the piece and in the tape. When there are affiliate links, they will be disclosed above the fold. Neither exists today.</p>',
'<h2>Contact</h2><p>Everything: <a href="mailto:info@garbatrage.com">info@garbatrage.com</a>. We read it. We may not answer it, but we read it.</p></div>'
)
os.makedirs(os.path.join(STATIC,"about"),exist_ok=True)
open(os.path.join(STATIC,"about","index.html"),"w").write(
    layout("About · Garbatrage","Garbatrage is a satirical financial publication. That is the whole answer.", about, f"{SITE}/about/"))
print("wrote static/about/index.html")

# ---- Methodology (static/methodology/index.html) ----
meth=legal_body(
'<div class="kick">Resources · Methodology</div>',
'<h1>Methodology</h1>',
'<p class="chl">A methodology page usually exists to prove rigour. Ours exists to be honest about where the rigour stops, which is at the edge of the fiction and immediately.</p>',
'<div class="legal"><h2>The Garbatrage Industrial Average</h2><p>The GIA is a fictional price-weighted index of twenty-five fictional companies, all of them in or adjacent to the waste, hauling and reclamation economy. It is not a benchmark. It is not calculated by an exchange, licensed to anyone, or tracked by a fund.</p><p>Composition is discretionary and hand-picked by the desk. Constituents are added when a story needs them and removed when they stop being funny, which is the only rebalancing rule.</p>',
'<table><tr><th>Property</th><th>Value</th></tr><tr><td>Constituents</td><td>25, fixed</td></tr><tr><td>Weighting</td><td>Price-weighted, unequally and without justification</td></tr><tr><td>Rebalance</td><td>Discretionary</td></tr><tr><td>Base</td><td>38,221.07, chosen for texture</td></tr><tr><td>Real prices</td><td>None. Every number is invented.</td></tr></table>',
'<h2>Where real data appears</h2><p>The tape at the top of the page runs real instruments — major indices, FX, gold, crypto — from third-party providers. Those numbers are real, delayed, and not our fault. Everything below the tape is fiction. The two sit next to each other, which is the whole problem and the whole point.</p>',
'<h2>Mid-value</h2><p>"Mid-value" is our house doctrine: the position that value hides in unglamorous places, that the interesting trade is always in something with a smell, and that growth is what people yell about while the patient quietly buy bins. It has no academic basis. It has a lot of conviction.</p>',
'<h2>How a piece gets made</h2><ul><li><strong>Premise.</strong> The desk picks a real behaviour in finance and takes it one step past where it currently stops.</li><li><strong>Draft.</strong> Written against the register — no winking, no italics for irony, no explaining the joke in the final line.</li><li><strong>Continuity.</strong> Checked against the constituent file. Tickers, founding dates and anchors must not contradict earlier work.</li><li><strong>Edit.</strong> Human edit pass for rhythm. A piece that is accurate to the fiction but doesn\'t land gets cut, not fixed.</li><li><strong>Label.</strong> Satire tag in the masthead, disclaimer under the index, and the standard footer.</li></ul>',
'<h2>Machine involvement</h2><p>Drafting, art and production are machine-assisted. Editing is human. We do not publish unreviewed output, and we do not claim the reverse either — some of what you\'re reading started as a prompt, and the good lines are the ones a person kept.</p>',
'<div class="pull">Uncited statistics may have been invented to make a beat work. Assume this. It is faster than checking.</div>',
'<h2>What we would tell a lawyer</h2><p>Nothing here is advice. The GIA is not a real benchmark. Real company names appear only in the tape, alongside real prices. Read the <a href="/terms.html">Terms</a>.</p>',
'<p class="mt">Last updated 5 November 2026.</p></div>'
)
os.makedirs(os.path.join(STATIC,"methodology"),exist_ok=True)
open(os.path.join(STATIC,"methodology","index.html"),"w").write(
    layout("Methodology · Garbatrage","How the index is built, and how the stories are made.", meth, f"{SITE}/methodology/"))
print("wrote static/methodology/index.html")
# ---- Press (static/press/index.html) ----
press_body = ('<div class="kick">Company · Press</div>'
 '<h1>Press</h1>'
 '<p class="lede">Press is for things that happened. We publish things that mostly haven\'t. '
 'If you need to describe us anyway, use the language below and don\'t improve it.</p>'
 '<h2>Boilerplate</h2>'
 '<p>Garbatrage is a satirical financial publication covering a fictional market, reported straight. '
 'It publishes the Garbatrage Industrial Average, a fictional twenty-five-company index, alongside real '
 'market prices in its tape. Founded 2026. Independently owned by Garbatrage Media Group LLC.</p>'
 '<h2>The one thing to get right</h2>'
 '<p>We are satire, not analysis. Anything quoted from us should be attributed as such, and should not be '
 'presented as fact or as advice. A link is appreciated and a "satire" tag is not optional.</p>'
 '<h2>Assets</h2>'
 '<p>Mark, wordmark and colour references: <a href="mailto:info@garbatrage.com?subject=Press%20assets">request by email</a>. '
 'Please don\'t redraw the mark or set the name in a font we don\'t use.</p>'
 '<h2>Enquiries</h2>'
 '<p><a href="mailto:info@garbatrage.com">info@garbatrage.com</a> — subject line "Press." '
 'We answer press faster than we answer anything else, which is a failing and we know it.</p>'
 '<div class="disc">GARBATRAGE is a satirical publication. All quotes, indexes, tickers and figures '
 'are fabricated. Nothing herein is investment advice.</div>')
os.makedirs(os.path.join(STATIC,"press"),exist_ok=True)
open(os.path.join(STATIC,"press","index.html"),"w").write(
    layout("Press · Garbatrage","Press for a satirical financial publication.", press_body, f"{SITE}/press/"))
print("wrote static/press/index.html")

# ---- 404 ----
four_body = ('<div class="kick">Error</div>'
 '<h1>Nothing here.</h1>'
 '<p class="lede">This page does not exist. That is a fact we are prepared to defend, '
 'and it is the nearest thing on this site to a guarantee. If you were looking for something, '
 'it is probably in the <a href="/archive/">archive</a>, the '
 '<a href="/markets/">markets</a>, or a company page below the tape. What it is not is here.</p>')
open(os.path.join(STATIC,"404.html"),"w").write(
    layout("404 · Garbatrage","This page does not exist. It is probably in the archive or the markets.", four_body, f"{SITE}/404.html"))
print("wrote static/404.html")

# prune files NOT in the canonical static/ spec
import os as _os
KEYS = {"site.css","logo-cream.png","logo-black.png","monogram-cream.png","monogram-black.png",
        "seal-cream.png","seal-black.png","og-card.png","favicon-16.png","favicon-32.png",
        "favicon-180.png","icon-512.png","manifest.webmanifest"}
a = _os.path.join(STATIC,"assets")
pruned=[]
for f in _os.listdir(a):
    if f not in KEYS:
        _os.remove(_os.path.join(a,f)); pruned.append(f)
print("pruned from static/assets:", pruned if pruned else "none (clean)")
print("done static")

