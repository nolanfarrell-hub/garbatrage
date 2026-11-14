#!/usr/bin/env python3
"""Generate garbatrage.com/dump/ — The Morning Dump.

A deadpan video aggregate: the newest uploads from comedy/satire channels
(The Daily Show, Last Week Tonight, The Onion, SNL, Key & Peele, Hard Times),
pulled from YouTube's no-key RSS feeds and rendered in the navy register.

Run this BEFORE build_site.py; it writes data/dump.json which build_site
renders (the daily build itself never touches the network, so a YouTube
hiccup can't break the deploy — a stale/absent dump just renders a friendly
fallback). https://www.youtube.com/feeds/videos.xml?channel_id= works without
an API key and returns the 15 newest uploads per channel.
"""
import json, re, html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "dump.json"

# Channel -> display name, ordered loosely by how reliably-sketchy/funny the
# uploads skew. Keep the list tight: this page's only product is "funny."
CHANNELS = [
    ("UCfAOh2t5DpxVrgS9NQKjC7A", "The Onion"),
    ("UCdN4aXTrHAtfgbVG9HjBmxQ", "Key & Peele"),
    ("UCwWhs_6x42TyRM4Wstoq8HA", "The Daily Show"),
    ("UC3XTzVzaHQEd30rQbuvCtTQ", "Last Week Tonight"),
    ("UCqFzWxSCi39LnW1JKFR3efg", "Saturday Night Live"),
    ("UCSJtWSd-TfydTFExVbxAkMQ", "The Hard Times"),
]
UA = {"User-Agent": "Mozilla/5.0 (garbatrage-morning-dump build)"}
NS = {"yt": "http://www.youtube.com/xml/schemas/2015", "a": "http://www.w3.org/2005/Atom"}


def fetch(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    with urlopen(Request(url, headers=UA), timeout=20) as r:
        return ET.fromstring(r.read())


def iso(txt):
    try:
        return datetime.fromisoformat(txt.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def collect():
    videos = []
    for cid, label in CHANNELS:
        try:
            root = fetch(cid)
        except Exception as e:
            print(f"  warn: {label}: {e}")
            continue
        title = None
        for el in root.findall("a:title", NS):
            title = el.text
            break
        for entry in root.findall("a:entry", NS):
            vtitle = entry.findtext("a:title", default="", namespaces=NS)
            link = entry.find("a:link", NS).get("href", "")
            vid = (link.rstrip("/").rsplit("=", 1)[-1] if "=" in link else link.rstrip("/").rsplit("/", 1)[-1])
            pub = entry.findtext("a:published", default="", namespaces=NS)
            # thumbnail
            thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
            videos.append({
                "channel": label, "title": vtitle.strip(),
                "id": vid, "href": link, "thumb": thumb,
                "published": iso(pub).astimezone(timezone.utc).isoformat(),
            })
        print(f"  ok  {label}: {len(root.findall('a:entry', NS))} entries")
    videos.sort(key=lambda v: v["published"], reverse=True)
    return videos


def main():
    print("pull: gathering comedy feeds (no API key)...")
    videos = collect()
    print(f"pull: {len(videos)} videos across {len(CHANNELS)} channels")
    OUT.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(),
        "channels": len(CHANNELS),
        "videos": videos,
    }, ensure_ascii=False, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
