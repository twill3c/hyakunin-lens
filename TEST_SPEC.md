# TEST_SPEC.md — hyakunin-lens

<!-- scaffold template v1.8.0 から展開(2026-08-20)。以後このファイルはプロジェクトが育てる -->

## テスト一覧

| ID | 内容 | 対応要求 | ファイル |
|---|---|---|---|
| T-01 | データスキーマ検証: 100 名、必須キー、カテゴリ/ソース語彙、日付形式、URL 形式、各セクション最大 3 件、名前の重複なし | F-01 | tests/test_data.py |
| T-02 | 不変条件: 全セクション 0 件の人 0 名、meta 形状(updated_at は UTC ISO) | F-01, F-04 | tests/test_data.py |
| T-03 | 往復一致オラクル: `out/index.html` から P/CAT_LABEL/SRC/CATS を再抽出し `data/*.json` と完全一致 | F-02 | tests/test_build.py |
| T-04 | 出力健全性: プレースホルダ残存なし、件数行(データから算出)・カテゴリチップ 11 個・CUTOFF 日付の埋め込み、esc 関数と各 UI 部品の存在 | F-02, F-03, N-02 | tests/test_build.py |
| T-05 | 決定性: 2 回ビルドしてバイト一致 | N-01 | tests/test_build.py |
| T-06 | フィードパーサ煙テスト(RSS2.0 / Atom、koho-lens 移植分)と feed_items の整形 | F-07 | tests/test_update.py |
| T-07 | マージ規則: 成功種別のみ差し替え・失敗時は既存維持(劣化継続)・日付降順(不明末尾)・URL 重複排除・最大 3 件・入力非破壊・混合成否の run() | F-07 | tests/test_update.py |
| T-08 | sources.json スキーマ: 実在人物への参照・種別語彙(blog/substack/note/lab)・https フィード | F-06 | tests/test_data.py |
| T-09 | フッタ構成(koho-lens 準拠・画面最下部固定)と最終更新行の埋め込み | F-09 | tests/test_build.py |
| T-10 | YouTube 自動更新: 氏名語形の照合(中間イニシャル・漢字名)、タイトル一致ゲート、own/med 重複除外、最大 3 件・日付降順、日次バケット交替、エラー時劣化継続、入力非破壊 | F-10 | tests/test_youtube.py |

## 実行

```bash
python -m pytest -q
```
