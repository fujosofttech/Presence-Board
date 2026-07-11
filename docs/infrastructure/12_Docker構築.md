# 12_Docker構築手順

> Version: 1.0

---

# 1. 概要
本システムはローカル開発環境および本番環境（Oracle Cloud）で一貫した動作環境を保証するため、Docker / Docker Composeを採用している。
本ドキュメントでは、ローカル開発環境におけるDocker環境の構築手順および基本操作について説明する。

---

# 2. 前提要件
- **Docker**: v29.4以上推奨
- **Docker Compose**: v2.0以上推奨
- **OS**: Windows 10/11 (WSL2有効化済みであること) / macOS / Linux

---

# 3. 提供ファイル
プロジェクトルートにある以下のファイルを使用して環境を起動する。

- `Dockerfile`: Djangoアプリケーション実行環境の定義
- `docker-compose.yml`: DjangoおよびPostgreSQLデータベースコンテナの定義
- `.env`: データベース認証情報などの環境変数設定

---

# 4. 起動手順

## 4.1 環境変数ファイルの準備
リポジトリクローン直後は `.env` ファイルが存在しないため、テンプレートからコピーする。
```powershell
copy .env.example .env
```
※ ローカル開発用途であれば、デフォルト値のままで問題なく動作する。

## 4.2 コンテナの起動
以下のコマンドを実行し、イメージのビルドおよびコンテナのバックグラウンド起動を行う。
```powershell
docker compose up -d --build
```

## 4.3 データベースのマイグレーション
初回起動時、またはデータベースモデル変更時は、コンテナ内でマイグレーションを実行してテーブルを作成する。
```powershell
docker compose exec web python manage.py migrate
```

---

# 5. 動作確認

## 5.1 コンテナ起動状態の確認
以下のコマンドで、`presence_board_db` (PostgreSQL) と `presence_board_web` (Django) が動作しているか確認する。
```powershell
docker compose ps
```

## 5.2 APIドキュメント (Swagger UI) へのアクセス
ブラウザを開き、以下のURLへアクセスすることでAPI設計が正しく適用されているか確認できる。
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **OpenAPI Schema (JSON)**: `http://localhost:8000/api/schema/`

---

# 6. コンテナの停止・管理

- **コンテナの停止**:
  ```powershell
  docker compose down
  ```
- **コンテナ内のシェルに入る (Django)**:
  ```powershell
  docker compose exec web bash
  ```
- **ログの確認**:
  ```powershell
  docker compose logs -f web
  ```
- **データベースボリュームの初期化 (データを消去して再構築したい場合)**:
  ```powershell
  docker compose down -v
  ```
