FROM python:3.13-slim

# 作業ディレクトリ
WORKDIR /app

# システム依存パッケージ（psycopg2 のビルドに必要）
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 依存パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# プロジェクトをコピー
COPY . .

# ポート公開
EXPOSE 8000
