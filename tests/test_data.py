# -*- coding: utf-8 -*-
"""T-01 / T-02: data/people.json と data/meta.json のスキーマ・件数検証。"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

DATE_RE = re.compile(r"\d{4}-\d{2}(-\d{2})?$")
PERSON_REQUIRED = {"n", "c", "h", "bio", "own", "med", "yt"}
PERSON_OPTIONAL = {"note", "mnote", "ynote"}
ITEM_REQUIRED = {"d", "s", "t", "u"}
ITEM_OPTIONAL = {"o"}


@pytest.fixture(scope="module")
def people():
    return json.loads((ROOT / "data" / "people.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def meta():
    return json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8"))


def items(people):
    for p in people:
        for sec in ("own", "med", "yt"):
            for i in p[sec]:
                yield p, sec, i


# ---- T-01 スキーマ ----

def test_100_people(people):
    assert len(people) == 100


def test_person_keys(people):
    for p in people:
        keys = set(p.keys())
        assert PERSON_REQUIRED <= keys, f"{p.get('n')}: 必須キー欠落 {PERSON_REQUIRED - keys}"
        assert keys <= PERSON_REQUIRED | PERSON_OPTIONAL, f"{p['n']}: 未知キー {keys - PERSON_REQUIRED - PERSON_OPTIONAL}"
        assert p["n"].strip() and p["bio"].strip()


def test_no_duplicate_names(people):
    names = [p["n"] for p in people]
    assert len(names) == len(set(names))


def test_categories_in_vocab(people, meta):
    for p in people:
        assert p["c"] in meta["cats"], f"{p['n']}: 未知カテゴリ {p['c']}"
    assert set(meta["cat_label"]) == set(meta["cats"])


def test_item_shape(people, meta):
    for p, sec, i in items(people):
        keys = set(i.keys())
        assert ITEM_REQUIRED <= keys, f"{p['n']}/{sec}: 必須キー欠落"
        assert keys <= ITEM_REQUIRED | ITEM_OPTIONAL, f"{p['n']}/{sec}: 未知キー {keys - ITEM_REQUIRED - ITEM_OPTIONAL}"
        assert i["s"] in meta["src_label"], f"{p['n']}/{sec}: 未知ソース {i['s']}"
        assert i["t"].strip(), f"{p['n']}/{sec}: 空タイトル"


def test_dates(people):
    for p, sec, i in items(people):
        assert i["d"] == "不明" or DATE_RE.fullmatch(i["d"]), f"{p['n']}/{sec}: 不正日付 {i['d']!r}"


def test_urls(people):
    for p, sec, i in items(people):
        assert i["u"].startswith(("http://", "https://")), f"{p['n']}/{sec}: 不正URL {i['u']!r}"
    for p in people:
        assert p["h"] == "" or p["h"].startswith(("http://", "https://"))


def test_max_3_per_section(people):
    for p in people:
        for sec in ("own", "med", "yt"):
            assert len(p[sec]) <= 3, f"{p['n']}/{sec}: {len(p[sec])}件"


# ---- T-02 件数・不変条件(自動更新で件数は変動するため実数は固定しない)----

def test_sections_nonempty_overall(people):
    assert all(p["own"] or p["med"] or p["yt"] for p in people)


def test_meta_shape(meta):
    assert meta["collected_on"] == "2026-08-20"
    assert len(meta["cats"]) == 11
    if "updated_at" in meta:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", meta["updated_at"])


# ---- T-08 sources.json スキーマ ----

def test_sources_schema(people, meta):
    path = ROOT / "data" / "sources.json"
    if not path.exists():
        pytest.skip("sources.json 未生成")
    sources = json.loads(path.read_text(encoding="utf-8"))
    names = {p["n"] for p in people}
    for s in sources:
        assert set(s.keys()) >= {"n", "s", "feed"}, s
        assert s["n"] in names, f"実在しない人物: {s['n']}"
        assert s["s"] in {"blog", "substack", "note", "lab"}, s
        assert s["feed"].startswith("https://"), s
