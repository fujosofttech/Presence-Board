# Presence-Board

社内向けの行先掲示板（Web アプリケーション）。

社員の在籍状況（在席／客先／外出／会議／リモート／休暇 など）を一元管理し、
ブラウザから確認・更新できる業務システムです。

## コンセプト

本プロジェクトは **「人と AI が共同利用する業務システム」** を目指します。

- AI を第一級の利用者（First-class Citizen）として設計（AI First Design）
- REST API を唯一の業務インターフェースとする
- 社内のローカル AI サーバー（LLM）との連携を前提とする
- 将来的に MCP（Model Context Protocol）サーバーを追加可能な構成

また、本プロジェクトは **教育教材** としても利用されることを想定しています。

## 技術スタック（予定）

- バックエンド: Django + Django REST Framework
- データベース: PostgreSQL
- インフラ: Oracle Cloud Free / Docker
- リアルタイム通知: SSE（Server-Sent Events）
- API 仕様: OpenAPI 3.1（Swagger UI 提供）

## ドキュメント

設計ドキュメントは `docs/` 配下に格納しています。

```
docs/
├── requirements/     # 01 プロジェクト概要 / 02 要件定義 / 03 ユースケース
├── design/          # 04 画面設計 / 05 DB設計 / 06 API設計 / 07 認証設計 / 08 アーキテクチャ / 09 管理者機能設計
├── infrastructure/  # 11 Oracle Cloud / 12 Docker / 13 デプロイ
├── development/     # 14 テスト仕様書 / 15-17 AI 指示書 / 18 AI 連携設計
└── decisions/       # 00 Decision Log / ADR-0001〜0003
```

詳細は [CHANGELOG.md](./CHANGELOG.md) および `docs/` を参照してください。

## ライセンス

[MIT License](./LICENSE)
