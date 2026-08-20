# -*- coding: utf-8 -*-
"""own セクションの差し替えマージ(F-07 / T-07)。

規則:
- フィード収集に成功したソース種別(s)の既存項目は捨て、収集項目で置き換える
- それ以外の種別(x / linkedin / 未収集・失敗種別)は既存のまま維持(劣化継続)
- URL で重複排除し、日付降順(YYYY-MM は月初扱い、「不明」は末尾)で最大 3 件
"""

from __future__ import annotations

MAX_OWN = 3
UNKNOWN = "不明"


def sort_items(items: list[dict]) -> list[dict]:
    known = [i for i in items if i["d"] not in ("", UNKNOWN)]
    unknown = [i for i in items if i["d"] in ("", UNKNOWN)]
    known.sort(key=lambda i: i["d"] + ("-01" if len(i["d"]) == 7 else ""), reverse=True)
    return known + unknown


def merge_own(existing: list[dict], fetched: list[dict], fetched_ok_types: set[str]) -> list[dict]:
    """existing: 現在の own。fetched: 今回収集した項目(d/s/t/u)。
    fetched_ok_types: 今回フィード取得に成功したソース種別の集合。"""
    kept = [i for i in existing if i["s"] not in fetched_ok_types]
    seen: set[str] = set()
    merged: list[dict] = []
    for i in sort_items(list(fetched) + kept):
        if i["u"] in seen:
            continue
        seen.add(i["u"])
        merged.append(i)
    return merged[:MAX_OWN]
