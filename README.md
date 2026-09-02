# hyakunin-lens — 百人レンズ

**本番: https://hyakunin-lens.vercel.app**

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

- 「本人の発信」のうち **ブログ / Substack / note / 研究所ブログ**(`data/sources.json` に宣言された RSS・Atom フィード)は 6 時間ごと
- **YouTube 対談**は `collect-youtube.yml` が毎日 1 回、YouTube Data API v3 の検索で更新(`python -m src.youtube`)。
  品質ゲート(20分超の長尺のみ・タイトルに氏名の語形・直近180日・#shorts 排除)・own/med と重複する URL の除外・既存精選分との併合・日次 50 名ローテーション(2 日で一巡、無料クォータの 50% 以内)。
  リポジトリ Secret `YOUTUBE_API_KEY` が必要(未設定なら何もせず正常終了)
- 取得に失敗した人・宣言のない人は既存項目を維持する(劣化継続)
- X / LinkedIn・インタビューは 2026-08-20 収集のスナップショット(月次のエージェント再収集 routine で補完)

`out/index.html` は自己完結(外部リソース参照なし)。ブラウザで直接開ける。

## データの制約

- X / LinkedIn は直接取得不可。日付は投稿 ID(Snowflake)からの機械復元
- YouTube の公開日はほぼ取得不可(429)。日付「不明」の項目は「直近1か月」絞り込みの対象外
- 見出しの多くは英語原文の要約・和訳。原文はリンク先で確認のこと

詳細はページ内「データの制約」および [SPEC.md](SPEC.md) を参照。

## 法務・収集ポリシー

- 保存・表示するのは各人が公開する**見出し・リンク・日付のみ**(本文は取得も保存もしない)
- **見出しの著作権は各発信者に帰属する。** 要約・和訳を伴うものも同じで、原文の権利が及ぶ
- `LICENSE`(MIT)が及ぶのはコードと本アプリの生成物(名簿・分類・出荷 HTML の組み立て)で
  あって、`out/index.html` に載る見出しではない
- 各項目は発信元へのリンクにする
