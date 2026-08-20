# -*- coding: utf-8 -*-
"""T-03 / T-04 / T-05: ビルド出力の往復一致オラクルと健全性・決定性。"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from build import build, counts_line, load  # noqa: E402


@pytest.fixture(scope="module")
def html():
    build()
    return (ROOT / "out" / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def data():
    return load()


def slice_json(src: str, start_marker: str, end_marker: str) -> str:
    i = src.index(start_marker) + len(start_marker)
    return src[i:src.index(end_marker, i)].strip()


# ---- T-03 往復一致オラクル ----

def test_roundtrip_people(html, data):
    people, meta = data
    assert json.loads(slice_json(html, "const P = ", ", CAT_LABEL =")) == people
    assert json.loads(slice_json(html, "CAT_LABEL = ", ", SRC =")) == meta["cat_label"]
    assert json.loads(slice_json(html, "SRC = ", ", CATS =")) == meta["src_label"]
    assert json.loads(slice_json(html, "CATS = ", ";")) == meta["cats"]


# ---- T-04 出力健全性 ----

PLACEHOLDERS = ["__PEOPLE__", "__CAT_LABEL__", "__SRC__", "__CATS__",
                "__COUNTS__", "__COLLECTED__", "__CUTOFF_1M__", "__CAT_CHIPS__"]


def test_no_placeholders(html):
    for ph in PLACEHOLDERS:
        assert ph not in html, f"プレースホルダ残存: {ph}"


def test_counts_line_embedded(html, data):
    people, _ = data
    line = counts_line(people)
    assert "237" in line and "746" in line
    assert line in html


def test_cat_chips(html, data):
    _, meta = data
    for c in meta["cats"]:
        assert f'data-cat="{c}"' in html, f"カテゴリチップ欠落: {c}"
    assert html.count('data-cat="') == len(meta["cats"]) + 1  # +1 = ALL


def test_cutoff_embedded(html, data):
    _, meta = data
    assert f'const CUTOFF_1M = "{meta["cutoff_1m"]}"' in html


def test_ui_parts(html):
    for needle in ('id="q"', 'id="fOwn"', 'id="fMed"', 'id="fYt"',
                   'id="f2026"', 'id="f1m"', "const esc", "function render()"):
        assert needle in html, f"UI 部品欠落: {needle}"


def test_self_contained(html):
    for needle in ("<link", "src=\"http", "@import", "fetch("):
        assert needle not in html, f"外部参照の疑い: {needle}"


# ---- T-05 決定性 ----

def test_deterministic(html):
    first = (ROOT / "out" / "index.html").read_bytes()
    build()
    assert (ROOT / "out" / "index.html").read_bytes() == first
