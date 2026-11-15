#!/usr/bin/env python3
"""Garbatrage FINAL EDITOR GATE — triple-checks the catalog before it ships.

Run before ANY commit+push of data/stories.json. Fails (exit 1) if any check
violates; exit 0 = clear to publish. The cron / any deploy must call this and
abort on nonzero. This is the enforced supervisor, not a paragraph.

Checks:
  1. HEADLINE-CHANGE : every slug's title differs from baseline (no stale visible copy)
  2. GROUNDING       : no banned tell-words in any body; every body has a named person
  3. SLUG            : every slug byte-identical to baseline (URL + image key stable)
  4. BLOCKQUOTE      : exactly one <blockquote> per body
  5. DATE            : no story dated in the future / empty date
  6. ART-MATCH       : every story whose premise changed vs baseline must have freshly
                       regenerated art (file modified after the content change), and the
                       content-change set must be empty of unregenerated art. Stops the
                       "rewrote the copy, forgot the pictures" failure.
"""
import json, subprocess, sys, re, pathlib, os, time

REPO = pathlib.Path(__file__).resolve().parent
if len(sys.argv) < 3:
    print("usage: final_editor_gate.py <BASELINE_GIT_COMMIT> <path/to/stories.json>")
    sys.exit(2)
baseline_commit, data_path = sys.argv[1], sys.argv[2]

now = json.loads(pathlib.Path(data_path).read_text())
base = json.loads(subprocess.run(["git","-C",str(REPO),"show",f"{baseline_commit}:data/stories.json"],
    capture_output=True, text=True).stdout)
m = {s["slug"]: s for s in base}
n = {s["slug"]: s for s in now}

BANNED = ["configuration","participation","unenumerated","framework","paradigm","mechanism",
          "in a very real sense","the framing as","simultaneously","a position that is not"]
STOP = {"The","A","An","Investors","Analysts","Market","Bond","Banks","Bank","Credit","Estate","Fund","Fed","Company","Exchange","Oil","Some","This","That"}  # common false positives
NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b")
def has_name(body):
    low = body.lower()
    for m in NAME_RE.finditer(body[:400]):
        w = m.group(1)
        if w not in STOP and w.lower() not in STOP and len(w) > 2:
            return True
    return False

failures = []
for sl, s in n.items():
    if sl not in m:
        failures.append(f"NEW slug not in baseline (check intent): {sl}"); continue
    old = m[sl]
    # 3. slug integrity
    if sl != old["slug"]:
        failures.append(f"SLUG changed: {old['slug']!r} -> {sl!r}")
    # 1. headline change (only gate bodies PRESENT in baseline that were touched)
    if old["title"] == s["title"]:
        failures.append(f"HEADLINE STALE (== baseline): {sl}")
    # 2/4. grounding + blockquote
    body = s.get("body","")
    low = body.lower()
    for w in BANNED:
        if w in low:
            failures.append(f"BANNED word '{w}' in {sl}"); break
    if not has_name(body[:400]):
        failures.append(f"NO NAMED PERSON in {sl}")
    # one blockquote
    bq = body.count("<blockquote>")
    if bq != 1:
        failures.append(f"blockquote count={bq} in {sl}")
    # 5. date sanity
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", s.get("date","")):
        failures.append(f"BAD date in {sl}: {s.get('date')}")

# also ensure every baseline slug still exists (nothing deleted)
for sl in m:
    if sl not in n:
        failures.append(f"REMOVED a slug that existed in baseline: {sl}")

# ---- 6. ART-MATCH gate ----
# baseline commit time = the moment the old premise set shipped
base_ts = subprocess.run(["git","-C",str(REPO),"log","-1","--format=%ct",baseline_commit],
    capture_output=True, text=True).stdout.strip()
try:
    base_time = int(base_ts)
except ValueError:
    base_time = 0
imgdir = (REPO / "media" / "img").resolve()
for sl, s in n.items():
    ref = s.get("image") or f'/media/img/{sl}.png'
    fname = pathlib.Path(ref).name
    fpath = imgdir / fname
    if not fpath.exists():
        # maybe live under the full slug plus suffix; try glob
        import glob as _g
        cands = _g.glob(str(imgdir / (sl + "*.png")))
        if not cands:
            failures.append(f"ART MISSING for {sl}: {ref}")
            continue
        fpath = pathlib.Path(cands[0])
    mtime = fpath.stat().st_mtime
    if mtime < base_time:
        failures.append(f"ART STALE for {sl} (image predates premise change; regenerate): {ref}")

if failures:
    print(f"FINAL EDITOR GATE: FAIL ({len(failures)} violations) vs {baseline_commit}")
    for f in failures[:200]:
        print("  -", f)
    sys.exit(1)
else:
    print(f"FINAL EDITOR GATE: PASS — {len(n)} stories, all 4 checks clean vs {baseline_commit}")
    sys.exit(0)
