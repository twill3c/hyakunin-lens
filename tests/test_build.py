# -*- coding: utf-8 -*-
"""T-03 / T-04 / T-05: ビルド出力の往復一致オラクルと健全性・決定性。"""
import json
import re
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
                "__COUNTS__", "__COLLECTED__", "__CUTOFF_1M__", "__CAT_CHIPS__",
                "__UPDATED__", "__WALKTHROUGH_URL__", "__BLUEPRINT_URL__",
                "__FEED_UPDATED__", "__YT_UPDATED__", "__RECOLLECT_UPDATED__"]


def test_no_placeholders(html):
    for ph in PLACEHOLDERS:
        assert ph not in html, f"プレースホルダ残存: {ph}"


def test_counts_line_embedded(html, data):
    people, _ = data
    line = counts_line(people)
    assert re.fullmatch(r"100名 · 本人の発信 \d+件 · インタビュー/動画 \d+件 · "
                        r"YouTube対談 \d+件 · 合計 \d+件 · すべて0件の人 \d+名", line)
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


# ---- T-09 フッタ構成(koho-lens 準拠・F-09)----

def test_footer_structure(html):
    footer = html[html.index("<footer>"):html.index("</footer>")]
    for needle in ("MIT License", "© 2026 坂田哲朗",
                   "https://github.com/twill3c/hyakunin-lens",
                   "hyakunin-lens の歩き方", "hyakunin-lens 設計図",
                   "https://app-menu-amber.vercel.app", "App Menu"):
        assert needle in footer, f"フッタ要素欠落: {needle}"


def test_updated_line(html):
    assert "最終更新 " in html and "6 時間ごと" in html


def test_layer_timestamps_dynamic(html, data):
    # 三層の実行日は meta から動的に埋まる。未実行の層は「未実行」表示(F-09)
    from build import layer_jst
    _, meta = data
    for key in ("feed_updated_at", "youtube_updated_at", "recollect_updated_at"):
        assert layer_jst(meta, key) in html
    assert layer_jst({}, "recollect_updated_at") == "未実行"
    assert "収集のスナップショット" not in html  # 恒久的に誤りになりうる固定文言の禁止


def test_footer_fixed(html):
    # フッタは常に画面最下部に固定表示(F-09)。本文側に逃げ余白があること
    assert "footer{position:fixed" in html
    assert "padding:20px 24px 96px" in html


# ---- T-05 決定性 ----

def test_deterministic(html):
    first = (ROOT / "out" / "index.html").read_bytes()
    build()
    assert (ROOT / "out" / "index.html").read_bytes() == first
