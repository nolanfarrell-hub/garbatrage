#!/usr/bin/env bash
# Deploy the garbatrage URL-redirect Worker.
# Single source of truth for the redirect map: static/_redirects.
# Worker template: worker/redirect.js (keeps the __REDIRECTS__ placeholder).
# Generated output: worker/dist/redirect.js — deployed to zone garbatrage.com.
set -euo pipefail
cd "$(dirname "$0")/.."

WRANGLER="${WRANGLER:-/Users/nolanfarrell/sites/garbatrage-social/node_modules/.bin/wrangler}"
[ -x "$WRANGLER" ] || { echo "wrangler not found at $WRANGLER"; exit 1; }

# --- build the redirect map from _redirects ---
MAPJS=$(python3 - <<'PY'
import json, sys
pairs = []
for line in open("static/_redirects"):
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    p = s.split()
    if len(p) >= 3 and p[2] == "301":
        pairs.append([p[0], p[1]])
print("new Map(" + json.dumps(pairs) + ")")
PY
)

# --- substitute into the template -> dist ---
mkdir -p worker/dist
python3 - "$MAPJS" <<'PY'
import sys
mapjs = sys.argv[1]
tmpl = open("worker/redirect.js").read()
assert "__REDIRECTS__" in tmpl, "template must keep the __REDIRECTS__ placeholder"
open("worker/dist/redirect.js", "w").write(tmpl.replace("__REDIRECTS__", mapjs))
PY

GENERATED_PAIRS=$(grep -o '\\[\\"/' worker/dist/redirect.js | wc -l | tr -d ' ')
echo "deploying garbatrage-redirect (redirect pairs baked: $GENERATED_PAIRS)"
"$WRANGLER" deploy --config worker/wrangler.toml worker/dist/redirect.js
