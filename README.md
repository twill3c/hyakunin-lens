# hyakunin-lens — 百人レンズ

AI研究者・エージェント実装者 100 名の「発信ダッシュボード」。各人の紹介文と、

1. **本人の発信** — ブログ / Substack / 研究所ブログ / X / LinkedIn
2. **インタビュー・ポッドキャスト・動画・講演**
3. **YouTube 対談動画**

を最大 3 件ずつ、カテゴリ絞り込み(11 分類)・全文検索・期間絞り込み付きの単一 HTML で一覧する。
データは 2026-08-20 収集のスナップショット(100 名・746 件)。

## 使い方

```bash
python src/build.py                  # data/*.json → out/index.html
python -m src.update                 # フィード収集 → own 差し替え → 再ビルド
python tools/discover_feeds.py       # フィード自動発見(sources.json を育てる)
python -m pytest -q                  # スキーマ検証 + 往復一致オラクル + マージ + 決定性
```

## 定期更新のしかけ

GitHub Actions(`.github/workflows/collect.yml`)が 6 時間ごとに `python -m src.update` を実行し、
差分があるときだけ `data/` + `out/` をコミット → Vercel の Git 連携が自動デプロイする。

- 更新対象は「本人の発信」のうち **ブログ / Substack / note / 研究所ブログ**(`data/sources.json` に宣言された RSS・Atom フィード)のみ
- フィード取得に失敗した人・宣言のない人は既存項目を維持する(劣化継続)
- X / LinkedIn / YouTube・インタビューは 2026-08-20 収集のスナップショットのまま

`out/index.html` は自己完結(外部リソース参照なし)。ブラウザで直接開ける。

## データの制約

- X / LinkedIn は直接取得不可。日付は投稿 ID(Snowflake)からの機械復元
- YouTube の公開日はほぼ取得不可(429)。日付「不明」の項目は「直近1か月」絞り込みの対象外
- 見出しの多くは英語原文の要約・和訳。原文はリンク先で確認のこと

詳細はページ内「データの制約」および [SPEC.md](SPEC.md) を参照。
