# CHANGELOG

本リポジトリの変更履歴を管理します。
形式は [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に準拠します。

## Version 1.0

### Added
- AI First Design の採用（AI を第一級の利用者として設計）
- Oracle Cloud Free の採成（インフラ基盤）
- REST API を唯一の業務インターフェースとして採用
- SSE（Server-Sent Events）の採用
- OpenAPI 3.1 仕様の公開方針
- `docs/` 設計ドキュメント群（requirements / design / infrastructure / development）
  - 01 プロジェクト概要
  - 02 要件定義
  - 03 ユースケース
  - 04 画面設計
  - 05 DB 設計
  - 06 API 設計（AI エージェント対応方針を含む）
  - 07 認証設計
  - 08 システムアーキテクチャ
  - 09 管理者機能設計
  - 11 Oracle Cloud 構築手順
  - 12 Docker 構築
  - 13 デプロイ手順
  - 14 テスト仕様書
  - 15 AI 開発指示書
  - 16 AI レビュー指示書
  - 17 AI テスト指示書
  - 18 AI 連携設計
- Decision Log（ADR-0001 〜 ADR-0003）
  - ADR-0001 クラウド選定
  - ADR-0002 自作 vs OSS
  - ADR-0003 SSE vs WebSocket
- LICENSE（MIT）
- 本 CHANGELOG

### Changed
- DB 設計を全面見直し
- PresenceHistory を 30 日保持へ変更
- Employee へ display_order を追加
- WorkLocation を追加
- 状態コードを言語非依存（PRESENT / CUSTOMER / OUT / MEETING / REMOTE / HOLIDAY / LEAVE / DIRECT_HOME）に統一

### Removed
- 不要な API エンドポイントを削除
