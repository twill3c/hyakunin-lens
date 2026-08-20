# TEST_SPEC.md — hyakunin-lens

<!-- scaffold template v1.8.0 から展開(2026-08-20)。以後このファイルはプロジェクトが育てる -->

## テスト一覧

| ID | 内容 | 対応要求 | ファイル |
|---|---|---|---|
| T-01 | データスキーマ検証: 100 名、必須キー、カテゴリ/ソース語彙、日付形式、URL 形式、各セクション最大 3 件、名前の重複なし | F-01 | tests/test_data.py |
| T-02 | 件数固定: own=237 / med=263 / yt=246 / 合計 746、全セクション 0 件の人 0 名 | F-01, F-04 | tests/test_data.py |
| T-03 | 往復一致オラクル: `out/index.html` から P/CAT_LABEL/SRC/CATS を再抽出し `data/*.json` と完全一致 | F-02 | tests/test_build.py |
| T-04 | 出力健全性: プレースホルダ残存なし、件数行・カテゴリチップ 11 個・CUTOFF 日付の埋め込み、esc 関数と各 UI 部品の存在 | F-02, F-03, N-02 | tests/test_build.py |
| T-05 | 決定性: 2 回ビルドしてバイト一致 | N-01 | tests/test_build.py |

## 実行

```bash
python -m pytest -q
```
