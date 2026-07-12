# 06_API・SSE設計

> この文書を唯一の正として実装すること。不明点は推測せず、本文中の `TODO` に記録すること。
> Django標準機能を優先し、可読性・保守性・セキュリティを優先すること。
>
> プロジェクト名: 社内行先・在席管理システム（Internal Presence Management System）
> リポジトリ名: presence-board

---

## 1'. HTTPS化方針（確定）

`01_プロジェクト概要.md` の方針通り、本番運用はHTTPS必須とする。

- **Nginx + Let's Encrypt（Certbot）** でTLS証明書を無料取得・自動更新する。
  - Oracle Cloud Always Free上で完結でき、追加コストが発生しない
  - Certbotの自動更新（cron／systemd timer）により証明書の失効を防ぐ
- Django側は `SECURE_SSL_REDIRECT = True` を設定し、HTTP接続を強制的にHTTPSへリダイレクトする。
- Cookie属性の `Secure` フラグ（`07_認証・セキュリティ詳細.md` 4章）はこの方針確定により有効化する。
- `TODO`: ドメイン名の取得・DNS設定（Oracle Cloudの固定IPに対するドメイン紐付け）は運用側で準備する。

---

## 0. この文書の位置づけ

`04_画面設計.md` の画面仕様、`05_データモデル.md` のテーブル設計を前提に、
状態更新等のAPIインターフェースと、SSEによるリアルタイム配信の仕様を確定する。

---

## 1. API方針

- **REST API（JSON固定）** を基本方針とし、文字コードは **UTF-8**、日時は **ISO8601** とする。
- OpenAPI 3.1 仕様を採用し、Swagger UI を提供する。
- Django REST Framework（DRF）を利用する。
- 認証: 
  - ユーザー向け（ブラウザ経由）: セッション認証
  - AI エージェント向け: Bearer Token 認証
- エラー応答形式（必須）:
  ```json
  {
    "error_code": "E0001",
    "message": "エラーメッセージ",
    "details": {}
  }
  ```
- IP制限: ネットワーク層（Oracle Cloudのセキュリティリスト／ファイアウォール等）で実現する前提とする。

---

## 2. 主要エンドポイント一覧

| メソッド | パス | 概要 |
|---|---|---|
| GET | `/api/presence/` | 一覧画面表示用データ取得（課タブ・グループ・氏名・状態・行先・戻り予定） |
| PATCH | `/api/presence/me/` | 自分の現在の状態を更新（インライン編集の保存） |
| GET | `/api/destinations/favorites/` | 自分のお気に入り行先テンプレート取得 |
| POST | `/api/destinations/favorites/` | お気に入り行先の追加 |
| DELETE | `/api/destinations/favorites/{id}/` | お気に入り行先の削除 |
| GET | `/api/destinations/recent/` | 直近30日の使用履歴からの自動候補取得（履歴テーブルから動的に集計） |
| GET | `/api/scheduled-status/` | 自分の事前登録一覧取得 |
| POST | `/api/scheduled-status/` | 事前登録の新規作成 |
| PATCH | `/api/scheduled-status/{id}/` | 事前登録の変更（対象日より前のみ） |
| DELETE | `/api/scheduled-status/{id}/` | 事前登録の取消（対象日より前のみ） |
| GET | `/api/events/stream/` | SSEストリーム（一覧画面のリアルタイム更新） |

---

## 3. `PATCH /api/presence/me/` 詳細

### リクエスト例
```json
{
  "status": "out",
  "destination": "〇〇商事",
  "return_time": "2026-07-10T15:00:00+09:00"
}
```

### バリデーション（Service層で実装、`01_プロジェクト概要.md` 方針に従う）
| status | destination | return_time |
|---|---|---|
| present / leave / wfh / left_office | 空である必要あり | 空である必要あり |
| out | 必須 | 必須 |
| meeting / business_trip | 必須 | 任意 |
| direct_leave | 必須 | 常にnull（サーバ側で強制的にnull化） |

- バリデーション違反時は `400 Bad Request` を返し、フィールド単位のエラーメッセージを返却する。
- 保存成功時、`CurrentStatus` の更新に加え `StatusHistory` への追記をトランザクション内で行う（`05_データモデル.md` 4章）。
- 保存成功後、SSEイベントを発行する（4章参照）。

---

## 4. SSE設計

### エンドポイント
`GET /api/events/stream/`

### 方式
- Django標準の `StreamingHttpResponse` を用いて `text/event-stream` を返却する。
- 認証はセッションCookieで行う（通常のログイン状態を要求）。
- Nginx側で `proxy_buffering off;` 等、SSEに必要な設定を行う。
  - `TODO`: Nginx設定の詳細は `docker/` 配下の設定ファイル作成時に確定する。

### イベントペイロード例
```
event: presence_updated
data: {"employee_profile_id": 42, "status": "out", "destination": "〇〇商事", "return_time": "2026-07-10T15:00:00+09:00", "updated_at": "2026-07-10T13:05:00+09:00"}

```

### 配信範囲
- 全ログイン中クライアントに配信し、クライアント側（JS）で該当行のみ差分更新する（`04_画面設計.md` 4章の通り）。
- 課タブによる表示絞り込みはクライアント側の表示制御のみで行い、SSE配信自体は絞り込まない（シンプルさ優先）。

### 実現方式の選定
- 100名規模のため、Redis Pub/Sub等の外部ブローカーは導入せず、Django単体プロセス内でのイベント配信（例: `django-eventstream` 等のライブラリ、またはシンプルな自作実装）を検討する。
  - `TODO`: Oracle Cloud Free（ARM 4CPU/24GB）上でGunicornのワーカープロセスが複数になる場合、プロセス間でのイベント共有が必要になる。ワーカー数を1に固定するか、Redis等の軽量ブローカーを追加導入するかは、実装時の負荷試算を踏まえて確定する。

---

## 5. 事前登録反映バッチとAPIの関係

- `03_業務フロー.md` / `05_データモデル.md` で言及した「対象日の朝の自動反映バッチ」は、Django管理コマンド（`python manage.py apply_scheduled_status`）として実装し、cron等で定期実行する。
- バッチが `CurrentStatus` を更新した際も、通常のAPI経由の更新と同様にSSEイベントを発行し、ログイン中の全クライアントへリアルタイム反映する。
- `TODO`: バッチの実行時刻（例: 06:00 JST）は運用側で確定（`03_業務フロー.md` のTODOと共通）。

---

## 6. エラーハンドリング方針

| ステータスコード | ケース |
|---|---|
| 400 | バリデーションエラー（行先未入力等） |
| 401 | 未ログイン |
| 403 | 他人の状態を更新しようとした等の権限エラー |
| 404 | 存在しないリソースへのアクセス（他人の事前登録IDを指定等） |
| 500 | サーバ内部エラー |

- APIレスポンスのエラー形式はDRF標準のエラーフォーマットに準拠する。

---

## 7. 本章で確定した仕様のまとめ（差分）

| 項目 | 内容 |
|---|---|
| API方式 | REST API（DRF推奨） |
| IP制限 | ネットワーク層のみ、アプリ側二重チェックなし |
| リアルタイム更新 | SSE、`StreamingHttpResponse`ベース |
| HTTPS方針 | 確定。Nginx + Let's Encrypt（Certbot）でTLS証明書を無料取得・自動更新 |

---

## 8. 未確定事項（TODO一覧）

- [ ] DRF採用可否（Django標準機能優先方針との整合）
- [ ] Nginx側のSSE用設定詳細
- [ ] Gunicornワーカー数とSSEイベント共有方式（単一プロセス固定 or Redis等導入）
- [ ] 事前登録反映バッチの実行時刻

---

## 12. AI エージェント対応方針

本システムは AI First Design の原則に基づき、AI エージェントが第一級の利用者として操作可能なAPIを提供する。

- **OpenAPI 公開**: OpenAPI 3.1 に準拠した仕様書 (`openapi.yaml` などを想定) を公開し、AI がAPIの仕様を自己解釈できるようにする。
- **API バージョニング**: 将来の仕様変更に備え、URIにバージョン（例: `/api/v1/...`）を含める。
- **Bearer Token 認証**: AI エージェントはセッションに依存せず、APIキー（Bearer Token）を用いてAPIにアクセスする。
- **MCP サーバー連携**: 将来的に Model Context Protocol (MCP) サーバーを追加し、AI がツールとして本システムの機能 (`presence.update()`, `presence.search()` 等) を透過的に利用できる構造を見据えて実装する。

---

## 13. 次のステップ

- `07_認証・セキュリティ詳細.md` にて、ログイン・OTP・セッション管理および AI 用 Token 管理の実装詳細を確定する。
