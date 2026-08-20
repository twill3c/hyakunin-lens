# -*- coding: utf-8 -*-
"""T-10: YouTube 自動更新(名前一致ゲート・ローテーション・劣化継続)— オフライン。"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.youtube import (  # noqa: E402
    name_variants, run_yt, search_person, title_matches, todays_bucket,
)


def api_body(*videos):
    return json.dumps({"items": [
        {"id": {"videoId": v[0]}, "snippet": {
            "title": v[1], "publishedAt": v[2], "channelTitle": v[3]}}
        for v in videos
    ]}).encode()


# ---- 名前照合 ----

def test_name_variants():
    assert name_variants("Fei-Fei Li 李飛飛") == ["Fei-Fei Li", "李飛飛"]
    assert name_variants("Michael I. Jordan") == ["Michael I. Jordan", "Michael Jordan"]
    assert name_variants("秋葉拓哉") == ["秋葉拓哉"]


def test_title_gate():
    assert title_matches("No Priors Ep. 12 | With Noam Shazeer", "Noam Shazeer")
    assert title_matches("AI最前線・李飛飛が語る", "Fei-Fei Li 李飛飛")
    assert not title_matches("Top 10 AI news of the week", "Noam Shazeer")
    assert not title_matches("Noam Shazeer leaves! #Shorts", "Noam Shazeer")


def test_search_params_quality_gate():
    urls = []
    def capture(url):
        urls.append(url)
        return api_body()
    search_person("Jane Roe", "k", capture, published_after="2026-02-21T00:00:00Z")
    assert "videoDuration=long" in urls[0]
    assert "order=relevance" in urls[0]
    assert "publishedAfter=2026-02-21T00%3A00%3A00Z" in urls[0]


def test_search_person_filters_and_unescapes():
    body = api_body(
        ("v1", "Interview &amp; more with Jane Roe", "2026-08-01T00:00:00Z", "PodcastX"),
        ("v2", "Unrelated video", "2026-08-02T00:00:00Z", "Other"),
    )
    items = search_person("Jane Roe", "k", lambda url: body)
    assert len(items) == 1
    assert items[0] == {"d": "2026-08-01", "t": "Interview & more with Jane Roe",
                        "u": "https://www.youtube.com/watch?v=v1", "s": "yt", "o": "PodcastX"}


# ---- run_yt ----

def person(n, idx_urls=()):
    return {"n": n, "c": "基礎", "h": "", "bio": "b",
            "own": [{"d": "2026-01-01", "t": "t", "u": u, "s": "x"} for u in idx_urls],
            "med": [], "yt": [{"d": "不明", "t": "old", "u": "https://www.youtube.com/watch?v=old", "s": "yt"}]}


def test_run_yt_updates_only_bucket():
    people = [person("A"), person("B")]
    body = api_body(("v1", "Great talk with A and B", "2026-08-01T00:00:00Z", "Ch"))
    out, report = run_yt(people, "k", lambda url: body, bucket=0)
    assert out[0]["yt"][0]["u"] == "https://www.youtube.com/watch?v=v1"   # bucket 0 更新
    assert out[1]["yt"][0]["u"] == "https://www.youtube.com/watch?v=old"  # bucket 外は不変
    assert report["attempted"] == 1 and report["ok"] == 1


def test_run_yt_degrades_on_error_and_no_match():
    def boom(url):
        raise OSError("quota")
    people = [person("A")]
    out, report = run_yt(people, "k", boom, bucket=0)
    assert out[0]["yt"][0]["t"] == "old"
    assert report["ok"] == 0 and report["people"][0]["error"].startswith("OSError")


def test_run_yt_excludes_own_med_urls_and_caps():
    dup = "https://www.youtube.com/watch?v=dup"
    vids = [("dup", "A speaks", "2026-08-09T00:00:00Z", "Ch")] + [
        (f"v{i}", "A speaks again", f"2026-08-0{i}T00:00:00Z", "Ch") for i in range(1, 6)]
    people = [person("A", idx_urls=(dup,))]
    out, _ = run_yt(people, "k", lambda url: api_body(*vids), bucket=0)
    urls = [i["u"] for i in out[0]["yt"]]
    assert dup not in urls
    assert len(urls) == 3
    assert out[0]["yt"][0]["d"] == "2026-08-05"  # 日付降順


def test_run_yt_keeps_curated_when_few_new():
    people = [person("A")]
    body = api_body(("v1", "Long talk with A", "2026-08-01T00:00:00Z", "Ch"))
    out, _ = run_yt(people, "k", lambda url: body, bucket=0)
    urls = [i["u"] for i in out[0]["yt"]]
    assert urls == ["https://www.youtube.com/watch?v=v1",
                    "https://www.youtube.com/watch?v=old"]  # 既存の精選分が残る


def test_run_yt_does_not_mutate_input():
    people = [person("A")]
    before = json.dumps(people, ensure_ascii=False)
    run_yt(people, "k", lambda url: api_body(("v1", "A talk", "2026-08-01T00:00:00Z", "C")), bucket=0)
    assert json.dumps(people, ensure_ascii=False) == before


def test_bucket_alternates():
    assert todays_bucket(datetime(2026, 8, 20)) != todays_bucket(datetime(2026, 8, 21))
