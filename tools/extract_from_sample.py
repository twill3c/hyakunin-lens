# -*- coding: utf-8 -*-
"""サンプル HTML(ai100feeddashboard.html)から P / CAT_LABEL / SRC / CATS を抽出し
data/people.json と data/meta.json に書き出す一回限りの移行ツール。"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slice_json(src: str, start_marker: str, end_marker: str) -> str:
    i = src.index(start_marker) + len(start_marker)
    j = src.index(end_marker, i)
    return src[i:j].strip()


def main(sample_path: str) -> None:
    src = Path(sample_path).read_text(encoding="utf-8")
    people = json.loads(slice_json(src, "const P = ", ", CAT_LABEL ="))
    cat_label = json.loads(slice_json(src, "CAT_LABEL = ", ", SRC ="))
    src_label = json.loads(slice_json(src, "SRC = ", ", CATS ="))
    cats = json.loads(slice_json(src, "CATS = ", ";"))

    cutoff = re.search(r'CUTOFF_1M = "([0-9-]+)"', src).group(1)

    (ROOT / "data").mkdir(exist_ok=True)
    with open(ROOT / "data" / "people.json", "w", encoding="utf-8") as f:
        json.dump(people, f, ensure_ascii=False, indent=1)
        f.write("\n")
    meta = {
        "collected_on": "2026-08-20",
        "cutoff_1m": cutoff,
        "cats": cats,
        "cat_label": cat_label,
        "src_label": src_label,
    }
    with open(ROOT / "data" / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
        f.write("\n")

    own = sum(len(p["own"]) for p in people)
    med = sum(len(p["med"]) for p in people)
    yt = sum(len(p["yt"]) for p in people)
    print(f"people={len(people)} own={own} med={med} yt={yt} total={own+med+yt}")


if __name__ == "__main__":
    main(sys.argv[1])
