# -*- coding: utf-8 -*-
"""T-06 / T-07: フィードパーサとマージ・劣化継続(すべてオフライン)。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.feedparse import parse_feed  # noqa: E402
from src.merge import MAX_OWN, merge_own, sort_items  # noqa: E402
from src.update import feed_items, run  # noqa: E402

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>New post</title><link>https://ex.com/a</link>
<pubDate>Tue, 18 Aug 2026 10:00:00 GMT</pubDate></item>
<item><title>Old post</title><link>https://ex.com/b</link>
<pubDate>Mon, 05 Jan 2026 10:00:00 GMT</pubDate></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom entry</title><link rel="alternate" href="https://ex.com/c"/>
<published>2026-08-01T00:00:00Z</published></entry></feed>"""


# ---- T-06 フィードパーサ(移植の煙テスト)----

def test_parse_rss2():
    items = parse_feed(RSS)
    assert [i["url"] for i in items] == ["https://ex.com/a", "https://ex.com/b"]
    assert items[0]["date"] == "2026-08-18"


def test_parse_atom():
    assert parse_feed(ATOM)[0]["date"] == "2026-08-01"


def test_feed_items_shape():
    items = feed_items(RSS, "blog")
    assert items[0] == {"d": "2026-08-18", "t": "New post", "u": "https://ex.com/a", "s": "blog"}


def test_absolutize_schemeless_urls():
    from src.update import absolutize
    base = "https://ofir.io/feed.xml"
    assert absolutize("ofir.io/Post/", base) == "https://ofir.io/Post/"
    assert absolutize("/Post/", base) == "https://ofir.io/Post/"
    assert absolutize("//cdn.ex.com/p", base) == "https://cdn.ex.com/p"
    assert absolutize("https://ex.com/p", base) == "https://ex.com/p"


# ---- T-07 マージ規則 ----

X1 = {"d": "2026-02-05", "t": "x post", "u": "https://x.com/1", "s": "x"}
B_OLD = {"d": "2025-12-01", "t": "old blog", "u": "https://ex.com/old", "s": "blog"}
B_NEW = {"d": "2026-08-18", "t": "new blog", "u": "https://ex.com/a", "s": "blog"}
B_UNK = {"d": "不明", "t": "undated", "u": "https://ex.com/u", "s": "blog"}


def test_merge_replaces_fetched_type_keeps_others():
    out = merge_own([X1, B_OLD], [B_NEW], {"blog"})
    assert B_NEW in out and X1 in out and B_OLD not in out


def test_merge_degrades_on_failure():
    # 取得失敗(fetched 空・ok_types 空)→ 既存維持
    assert merge_own([X1, B_OLD], [], set()) == [X1, B_OLD]


def test_merge_sorts_desc_unknown_last():
    out = merge_own([], [B_UNK, B_OLD, B_NEW], {"blog"})
    assert out == [B_NEW, B_OLD, B_UNK]


def test_merge_caps_and_dedupes():
    many = [{"d": f"2026-08-{d:02d}", "t": "t", "u": f"https://ex.com/{d}", "s": "blog"}
            for d in range(1, 6)]
    out = merge_own([], many + [many[0]], {"blog"})
    assert len(out) == MAX_OWN
    assert out[0]["d"] == "2026-08-05"


def test_sort_items_month_precision():
    a = {"d": "2026-08", "t": "", "u": "1", "s": "blog"}
    b = {"d": "2026-07-31", "t": "", "u": "2", "s": "blog"}
    assert sort_items([b, a]) == [a, b]


# ---- T-07 run(): 劣化継続と exit 条件 ----

PEOPLE = [
    {"n": "Alice", "c": "基礎", "h": "https://alice.dev", "bio": "b",
     "own": [X1, B_OLD], "med": [], "yt": []},
    {"n": "Bob", "c": "基礎", "h": "https://bob.dev", "bio": "b",
     "own": [B_OLD], "med": [], "yt": []},
]
SOURCES = [
    {"n": "Alice", "s": "blog", "feed": "https://alice.dev/feed", "site": "https://alice.dev"},
    {"n": "Bob", "s": "blog", "feed": "https://bob.dev/feed", "site": "https://bob.dev"},
]


def fake_fetch(url):
    if "alice" in url:
        return RSS
    raise OSError("connection refused")


def test_run_mixed_success():
    people, report = run(PEOPLE, SOURCES, fetch=fake_fetch, now="2026-08-20T12:00:00Z")
    alice, bob = people
    assert alice["own"][0]["u"] == "https://ex.com/a"      # フィード反映
    assert X1 in alice["own"]                               # x は維持
    assert bob["own"] == [B_OLD]                            # 失敗 → 劣化継続
    assert report["ok"] == 1 and report["fail"] == 1
    assert report["sources"][1]["error"].startswith("OSError")


def test_run_does_not_mutate_input():
    before = [dict(p) for p in PEOPLE]
    run(PEOPLE, SOURCES, fetch=fake_fetch, now="")
    assert PEOPLE == before
