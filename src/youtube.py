# -*- coding: utf-8 -*-
"""YouTube 対談セクションの自動更新(F-10): python -m src.youtube

YouTube Data API v3 の search.list で各人の出演動画を検索し、
誤帰属ゲート(動画タイトルに氏名が含まれること)を通過したものだけで
yt セクションを差し替える。検索失敗・合格 0 件の人は既存維持(劣化継続)。

- クォータ: search.list は 100 units/回。無料枠 10,000/日に収めるため
  1 回の実行で全体の半数(偶数日/奇数日で交替)だけを更新し、2 日で一巡する
- 環境変数 YOUTUBE_API_KEY が未設定なら何もせず exit 0(ローカル実行・CI 安全)
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .merge import sort_items

ROOT = Path(__file__).resolve().parents[1]
API = "https://www.googleapis.com/youtube/v3/search"
MAX_YT = 3
_CJK = re.compile(r"[぀-ヿ一-鿿]+")
_LATIN = re.compile(r"[A-Za-z][A-Za-z .'À-ɏ-]*[A-Za-z.]")


def name_variants(name: str) -> list[str]:
    """氏名の照合語形。'Fei-Fei Li 李飛飛' → ['Fei-Fei Li', '李飛飛']、
    'Michael I. Jordan' → ['Michael I. Jordan', 'Michael Jordan']。"""
    variants = []
    latin = _LATIN.search(name)
    if latin:
        v = latin.group().strip()
        variants.append(v)
        no_middle = re.sub(r"\s+[A-Z]\.\s+", " ", v)
        if no_middle != v:
            variants.append(no_middle)
    variants += _CJK.findall(name)
    return variants or [name]


def title_matches(title: str, name: str) -> bool:
    t = title.lower()
    return any(v.lower() in t for v in name_variants(name))


def search_person(name: str, key: str, fetch) -> list[dict]:
    """検索 → 名前一致ゲート通過分を新しい順で返す。API エラーは例外のまま上げる。"""
    q = urllib.parse.urlencode({
        "part": "snippet", "type": "video", "maxResults": 25, "order": "date",
        "q": f'"{name_variants(name)[0]}"', "key": key,
    })
    body = json.loads(fetch(f"{API}?{q}"))
    items = []
    for it in body.get("items", []):
        vid = it.get("id", {}).get("videoId")
        sn = it.get("snippet", {})
        title = html.unescape(sn.get("title", ""))
        if not vid or not title_matches(title, name):
            continue
        items.append({
            "d": (sn.get("publishedAt", "") or "")[:10] or "不明",
            "t": title,
            "u": f"https://www.youtube.com/watch?v={vid}",
            "s": "yt",
            "o": html.unescape(sn.get("channelTitle", "")),
        })
    return items


def todays_bucket(now: datetime) -> int:
    """偶数日 0 / 奇数日 1(UTC 通日)。"""
    return now.toordinal() % 2


def run_yt(people, key, fetch, bucket: int):
    """(people, report) を返す純関数コア。people は書き換えない。
    bucket に該当する人(index % 2 == bucket)だけを更新対象にする。"""
    out, status, ok = [], [], 0
    for idx, p in enumerate(people):
        if idx % 2 != bucket:
            out.append(p)
            continue
        rec = {"n": p["n"], "ok": False, "count": 0}
        try:
            found = search_person(p["n"], key, fetch)
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"[:200]
            found = []
        exclude = {i["u"] for i in p["own"] + p["med"]}
        accepted, seen = [], set()
        for i in found:
            if i["u"] in exclude or i["u"] in seen:
                continue
            seen.add(i["u"])
            accepted.append(i)
        if accepted:
            rec["ok"] = True
            rec["count"] = len(accepted)
            ok += 1
            q = dict(p)
            q["yt"] = sort_items(accepted)[:MAX_YT]
            out.append(q)
        else:
            out.append(p)  # 劣化継続
        status.append(rec)
    return out, {"bucket": bucket, "ok": ok, "attempted": len(status), "people": status}


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "hyakunin-lens/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> int:
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        print("youtube: YOUTUBE_API_KEY 未設定 — スキップ(exit 0)")
        return 0

    people = json.loads((ROOT / "data" / "people.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    bucket = todays_bucket(now)
    new_people, report = run_yt(people, key, http_get, bucket)

    (ROOT / "data" / "people.json").write_text(
        json.dumps(new_people, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    meta = json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8"))
    meta["updated_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    (ROOT / "data" / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    report["generated_at"] = meta["updated_at"]
    (ROOT / "data" / "youtube_status.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")

    sys.path.insert(0, str(ROOT / "src"))
    from build import build
    build()

    print(f"youtube: bucket {report['bucket']} — {report['ok']}/{report['attempted']} 名更新")
    for s in report["people"]:
        mark = "ok " if s["ok"] else "-- "
        print(f"  {mark}{s['n']}: {s['count']} 件 {s.get('error', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
