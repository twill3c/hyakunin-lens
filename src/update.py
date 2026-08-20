# -*- coding: utf-8 -*-
"""定期更新エントリポイント: python -m src.update(F-07)

data/sources.json の宣言フィードを収集し、成功種別だけ own を差し替えて
data/people.json を更新、meta.json の updated_at を進め、out/index.html を再生成する。
exit code: 全フィード失敗のみ 1(それ以外は劣化継続で 0)。
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .feedparse import parse_feed
from .merge import merge_own

ROOT = Path(__file__).resolve().parents[1]
UA = "hyakunin-lens/1.0 (+https://github.com/twill3c/hyakunin-lens)"
UNKNOWN = "不明"


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def read_json(name: str):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def write_json(name: str, obj) -> None:
    (ROOT / "data" / name).write_text(
        json.dumps(obj, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")


def absolutize(u: str, base: str) -> str:
    """フィード内 URL の絶対化。スキームなし・ホスト先頭(ofir.io/…)にも対応。"""
    if u.startswith(("http://", "https://")):
        return u
    if u.startswith("//"):
        return "https:" + u
    host = urllib.parse.urlparse(base).netloc
    if u.startswith(host + "/"):
        return "https://" + u
    return urllib.parse.urljoin(base, u)


def feed_items(raw: bytes, s: str, base: str = "") -> list[dict]:
    items = []
    for e in parse_feed(raw):
        if not (e["title"] and e["url"]):
            continue
        u = absolutize(e["url"], base)
        if u.startswith(("http://", "https://")):
            items.append({"d": e["date"] or UNKNOWN, "t": e["title"], "u": u, "s": s})
    return items


def run(people, sources, fetch=http_get, now=""):
    """(people, status) を返す純関数コア。people は書き換えず新リストを返す。"""
    by_name: dict[str, list[dict]] = {}
    status = []
    ok_count = 0
    sources = [s for s in sources if not s.get("skip")]
    for src in sources:
        rec = {"n": src["n"], "s": src["s"], "feed": src["feed"], "ok": False, "count": 0}
        try:
            items = feed_items(fetch(src["feed"]), src["s"], src["feed"])
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"[:200]
            items = []
        if items:
            rec["ok"] = True
            rec["count"] = len(items)
            ok_count += 1
            by_name.setdefault(src["n"], []).append({"s": src["s"], "items": items})
        status.append(rec)

    out_people = []
    for p in people:
        got = by_name.get(p["n"])
        if not got:
            out_people.append(p)
            continue
        fetched = [i for g in got for i in g["items"]]
        ok_types = {g["s"] for g in got}
        q = dict(p)
        q["own"] = merge_own(p["own"], fetched, ok_types)
        out_people.append(q)

    return out_people, {"generated_at": now, "ok": ok_count,
                        "fail": len(sources) - ok_count, "sources": status}


def main() -> int:
    people = read_json("people.json")
    meta = read_json("meta.json")
    sources = read_json("sources.json")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_people, report = run(people, sources, now=now)

    write_json("people.json", new_people)
    meta["updated_at"] = now
    meta["feed_updated_at"] = now
    write_json("meta.json", meta)
    write_json("update_status.json", report)

    sys.path.insert(0, str(ROOT / "src"))
    from build import build
    build()

    n_active = report["ok"] + report["fail"]
    n_skip = len(sources) - n_active
    print(f"update: {report['ok']}/{n_active} フィード成功"
          + (f"(skip {n_skip} 件)" if n_skip else ""))
    for s in report["sources"]:
        mark = "ok " if s["ok"] else "NG "
        print(f"  {mark}{s['n']} [{s['s']}] {s.get('count', 0)} 件 {s.get('error', '')}")
    return 0 if (report["ok"] > 0 or not sources) else 1


if __name__ == "__main__":
    sys.exit(main())
