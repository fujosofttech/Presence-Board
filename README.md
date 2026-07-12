# Presence-Board (社内所在掲示板)

社内向けのリアルタイム在席状態掲示板システム。
社員の在席状況（在席／在宅／外出／会議／休暇 など）を一元管理し、リアルタイムでの状態共有、バッチ処理による予定自動反映、監査ログの収集、および AI エージェント（ローカル LLM / MCP サーバー）連携をサポートします。

---

## 🚀 主な機能

1. **リアルタイム在席ボード (`PresenceBoard.vue`)**
   - 社員の状態（在席、リモート、外出など）を一覧表示。
   - 変更があった際は SSE (Server-Sent Events) を介してブラウザにリアルタイムに即時反映。
   - インクリメンタルな曖昧検索（日本語のステータス名や「さん」などの敬称ノイズを自動解釈）。
   - よく行く行先のお気に入り（Favorite）登録、最近の履歴からの素早い選択機能。
2. **自動状態反映バッチ (`apply_scheduled_status`)**
   - 予定（ScheduledStatus）を入力しておくと、日次バッチで自動的にその日の在席状態に反映し、SSE でブロードキャストされます。
3. **管理者ダッシュボード (`AdminDashboard.vue`)**
   - 部署（Department）、グループ（Group）、社員（Employee）、勤務場所（WorkLocation）、状態（StatusMaster）のマスタ登録・編集・削除機能。
4. **監査ログ機能 (`AuditLog`) & 在席履歴検索**
   - ログイン成否、在席状態変更、マスタデータ管理操作を Django シグナルで自動検知して `audit_log` テーブルに保存（実行ユーザー、対象、IPアドレス、AIエージェント情報を含む）。
   - 大量の履歴データを効率的に検索するためのインデックス設計、および `/api/v1/presence/history/` での `LimitOffsetPagination` によるページ分割。
5. **クリーンアップコマンド (`prune_old_data`)**
   - 容量肥大化対策として、設定された期限（履歴: 30日、監査ログ: 365日）を過ぎた古いレコードを一括削除するクリーンアップコマンド。
6. **AI エージェント & MCP サーバー連携**
   - セッションに依存しない Bearer Token 認証（DRF TokenAuthentication）によるAPIアクセスに対応。
   - AI による書き込み・ログイン時は監査ログに `[AI操作 - Token: ...]` が自動的に記録されます。
   - 将来的な MCP (Model Context Protocol) サーバー化を見据え、`apps/presence/services/mcp_tools.py` に AI が直接インポートして実行できる Python レベルのツール関数（`presence.update`, `presence.search`, `presence.list`, `employee.find`）を定義しています。

---

## 🛠 技術スタック

- **バックエンド:** Python 3.13 / Django 5.x / Django REST Framework
- **フロントエンド:** Vue 3 / Vite / Vuetify 3 / TypeScript
- **データベース:** PostgreSQL
- **キャッシュ/PubSub (任意):** Redis (接続失敗時は自動的にメモリベースの配信へ安全フォールバック)
- **リアルタイム配信:** SSE (Server-Sent Events)

---

## 📦 セットアップ・実行手順

### 1. バックエンド (Django)

1. **仮想環境の作成とパッケージインストール:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **データベースマイグレーション:**
   ```bash
   python manage.py migrate
   ```
3. **初期データ（状態コードマスタなど）の投入:**
   ```bash
   python manage.py loaddata initial_data.json
   ```
4. **ローカルサーバーの起動:**
   ```bash
   python manage.py runserver
   ```

### 2. フロントエンド (Vue.js)

1. **パッケージのインストール:**
   ```bash
   cd frontend
   npm install
   ```
2. **開発サーバーの起動:**
   ```bash
   npm run dev
   ```

---

## 🧪 テスト・品質検証

すべての検証・チェックが通ることを確認しています。

- **バックエンドテストの実行:**
  ```bash
  $env:POSTGRES_HOST="localhost"; python manage.py test
  ```
- **Linter (Ruff) によるチェック:**
  ```bash
  ruff check apps
  ```
- **型検査 (Mypy) によるチェック:**
  ```bash
  mypy apps
  ```
- **フロントエンドビルドチェック:**
  ```bash
  cd frontend
  npm run build
  ```

---

## 🤖 AI / MCP 連携の利用方法

### OpenAPI 仕様書の取得
本システムは OpenAPI 3.1 に準拠しています。以下のエンドポイントから常に最新の API 仕様を取得可能です。
- Swagger UI (ブラウザ動作): `/api/docs/`
- OpenAPI JSON スキーマ: `/api/schema/`

### AI 用 API Token の発行
ローカル LLM や AI エージェントから本システムを操作する場合、Django の API Token を使用します。
```bash
python manage.py drf_create_token <ユーザー名>
```
HTTP リクエスト時には、ヘッダーに `Authorization: Token <Tokenキー>` を指定します。

### MCP (Model Context Protocol) への接続設計
将来的に MCP サーバーを立てる際、`apps/presence/services/mcp_tools.py` に記述されている関数群をそのままインポートして MCP Tools として登録できます。
- `presence_update`: 在席状態の更新
- `presence_search`: 自然言語による社員検索
- `presence_list`: 在席状況一覧の取得
- `employee_find`: 特定社員の情報の取得

---

## 📄 ライセンス

[MIT License](./LICENSE)
