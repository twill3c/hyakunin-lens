# HARNESS_CHANGELOG.md — ハーネス改訂台帳(hyakunin-lens)

原則: **エージェントがミスをするたびに、そのミスが二度と起きないようハーネスを改良する。**
起票条件: 同一失敗コード累計 2 回(LL-10)、または severity S1(LL-12)。

---

## HC-001

| 項目 | 内容 |
|---|---|
| 起票日 | 2026-08-20 |
| トリガー | `DATA-SRC` × 2(loop_002: ofir.io フィードのスキームなし URL / amasad.me フィードの item link 欠落)— ツーストライク(LL-10) |
| 診断 | 個人ブログのフィードは企業サイトより品質のばらつきが大きい(スキームなし URL・link/guid 欠落・空 item 等)。フィード導入時(discover)の検証が「パース可能・1 件以上」だけで、**項目 URL の実用性**を検証していなかった |
| 改訂 | (1) `src/update.py` に `absolutize()` を追加 — スキームなし・ホスト先頭・`//` 形式を絶対化し、それでも http(s) にならない項目は除外 (2) `sources.json` に `skip`/`skip_reason` 機構を追加し、構造的に使用不能なフィードを理由付きで恒久無効化 (3) T-01(URL 形式)+ T-06(absolutize 単体)が検出網。AGENTS.md にデータ改訂手順として pytest 必須を明記済み |
| 種別 | src + schema(プロジェクト局所。フィード収集を持つ姉妹プロジェクト(koho-lens 等)は URL 絶対化を独自実装済みのため還流不要) |
| SCAFFOLD_VERSION | 変更なし(scaffold ブロック外の改訂) |
| 効果検証 | 実フィード 21/21 成功・pytest 32 件緑(2026-08-20)。以後 5 ループで同根本原因の DATA-SRC 再発 0 件なら Closed |
| propagation | hyakunin-lens ✅ |
| 状態 | Verifying |

---

## 記録上の注意(次ループへの申し送り)

- loop_002 で escalation イベントの記録がスキーマ違反(`reason`/`question` 必須)で 2 回拒否されたまま loop_end を先に記録してしまい、LL-09 により追記不能になった。**escalation は必須フィールド(reason, question)を先に確認してから記録し、loop_end はすべてのイベントが受理されたのを確認してから打つこと**(該当エスカレーション内容は「gh repo create / vercel deploy が権限クラシファイアに拒否され、cron 稼働と本番公開に人間の操作が必要」— 本台帳に証跡として残す)
