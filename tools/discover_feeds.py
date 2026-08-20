# -*- coding: utf-8 -*-
"""フィード自動発見ツール(F-06 の初期構築・随時再実行可)。

各人のホームページ(h)から RSS/Atom フィードを発見し、実際にパースできた
ものだけを data/sources.json に書き出す。X / LinkedIn / YouTube / 論文系
(scholar 等)はスキップ。既存 sources.json のエントリは保持し、新発見のみ追加する。

usage: python tools/discover_feeds.py [--limit N] [--only 名前部分一致]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.feedparse import parse_feed  # noqa: E402

UA = "hyakunin-lens/1.0 (+https://github.com/twill3c/hyakunin-lens)"
SKIP_HOSTS = ("x.com", "twitter.com", "linkedin.com", "youtube.com",
              "scholar.google", "github.com", "huggingface.co")
COMMON_PATHS = ("feed", "rss", "feed.xml", "atom.xml", "index.xml", "rss.xml")
LINK_RE = re.compile(
    r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*>', re.I)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def classify(feed_url: str, home: str) -> str:
    host = urllib.parse.urlparse(feed_url).netloc
    if "substack.com" in host or "substack.com" in home:
        return "substack"
    if "note.com" in host:
        return "note"
    return "blog"


def try_feed(url: str) -> int:
    """パース可能なら件数、不可なら 0。"""
    try:
        return len(parse_feed(http_get(url)))
    except Exception:
        return 0


def discover(home: str) -> str | None:
    host = urllib.parse.urlparse(home).netloc.lower()
    if any(s in host for s in SKIP_HOSTS):
        return None
    # 1) HTML の <link rel=alternate>
    try:
        html = http_get(home).decode("utf-8", "replace")
        for tag in LINK_RE.findall(html):
            m = HREF_RE.search(tag)
            if m:
                cand = urllib.parse.urljoin(home, m.group(1))
                if try_feed(cand):
                    return cand
    except Exception:
        pass
    # 2) 定番パス
    base = home if home.endswith("/") else home + "/"
    for p in COMMON_PATHS:
        cand = urllib.parse.urljoin(base, p)
        if try_feed(cand):
            return cand
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    people = json.loads((ROOT / "data" / "people.json").read_text(encoding="utf-8"))
    src_path = ROOT / "data" / "sources.json"
    sources = json.loads(src_path.read_text(encoding="utf-8")) if src_path.exists() else []
    have = {s["n"] for s in sources}

    found = 0
    tried = 0
    for p in people:
        if p["n"] in have or not p["h"]:
            continue
        if args.only and args.only.lower() not in p["n"].lower():
            continue
        host = urllib.parse.urlparse(p["h"]).netloc.lower()
        if any(s in host for s in SKIP_HOSTS):
            continue
        tried += 1
        if args.limit and tried > args.limit:
            break
        feed = discover(p["h"])
        if feed:
            s = classify(feed, p["h"])
            sources.append({"n": p["n"], "s": s, "feed": feed, "site": p["h"]})
            found += 1
            print(f"  + {p['n']} [{s}] {feed}")
        else:
            print(f"  - {p['n']}: フィード未発見 ({p['h']})")

    sources.sort(key=lambda s: s["n"])
    src_path.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"discover: 対象 {tried} 名中 {found} 名で新発見 → sources.json 計 {len(sources)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
