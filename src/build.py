# -*- coding: utf-8 -*-
"""data/people.json + data/meta.json + src/template.html → out/index.html を生成する。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load():
    people = json.loads((ROOT / "data" / "people.json").read_text(encoding="utf-8"))
    meta = json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8"))
    return people, meta


def counts_line(people):
    own = sum(len(p["own"]) for p in people)
    med = sum(len(p["med"]) for p in people)
    yt = sum(len(p["yt"]) for p in people)
    empty = sum(1 for p in people if not (p["own"] or p["med"] or p["yt"]))
    total = own + med + yt
    return (f"{len(people)}名 · 本人の発信 {own}件 · インタビュー/動画 {med}件 · "
            f"YouTube対談 {yt}件 · 合計 {total}件 · すべて0件の人 {empty}名")


def collected_jp(iso: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{y}年{m}月{d}日"


def _jst(iso: str, fmt: str) -> str:
    from datetime import datetime, timedelta, timezone
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=9))).strftime(fmt)


def updated_jst(meta) -> str:
    """meta.updated_at(UTC ISO)→ 'YYYY-MM-DD HH:MM JST'。未更新なら収集日。"""
    iso = meta.get("updated_at")
    if not iso:
        return f"{meta['collected_on']}(初回収集)"
    return _jst(iso, "%Y-%m-%d %H:%M JST")


def layer_jst(meta, key: str) -> str:
    """三層それぞれの最終実行日(JST)。未実行なら『未実行』。"""
    iso = meta.get(key)
    return _jst(iso, "%Y-%m-%d") if iso else "未実行"


def cat_chips(meta) -> str:
    return "\n  ".join(
        f'<span class="chip" data-cat="{c}">{meta["cat_label"].get(c, c)}</span>'
        for c in meta["cats"]
    )


def build() -> Path:
    people, meta = load()
    tpl = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    j = lambda v: json.dumps(v, ensure_ascii=False)
    html = (tpl
            .replace("__PEOPLE__", j(people))
            .replace("__CAT_LABEL__", j(meta["cat_label"]))
            .replace("__SRC__", j(meta["src_label"]))
            .replace("__CATS__", j(meta["cats"]))
            .replace("__COUNTS__", counts_line(people))
            .replace("__COLLECTED__", collected_jp(meta["collected_on"]))
            .replace("__UPDATED__", updated_jst(meta))
            .replace("__FEED_UPDATED__", layer_jst(meta, "feed_updated_at"))
            .replace("__YT_UPDATED__", layer_jst(meta, "youtube_updated_at"))
            .replace("__RECOLLECT_UPDATED__", layer_jst(meta, "recollect_updated_at"))
            .replace("__WALKTHROUGH_URL__", meta["links"]["walkthrough"])
            .replace("__BLUEPRINT_URL__", meta["links"]["blueprint"]))
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    dest = out / "index.html"
    dest.write_text(html.replace("__CAT_CHIPS__", cat_chips(meta)), encoding="utf-8")
    return dest


if __name__ == "__main__":
    dest = build()
    print(f"{dest} ({dest.stat().st_size:,} bytes)")
