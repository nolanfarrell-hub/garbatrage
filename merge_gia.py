import json
from pathlib import Path
p = Path("data/gia.json"); g = json.loads(p.read_text())
patch = json.loads(Path("data/gia-patch.json").read_text())
for c in g["constituents"]:
    if c["ticker"] in patch: c.update(patch[c["ticker"]])
p.write_text(json.dumps(g, indent=2, ensure_ascii=False), encoding="utf-8")
print("merged", len(patch))
