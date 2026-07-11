# 11_OracleCloud 構築手順

> Version: 1.0

---

# 1. 概要
本システムの本番運用環境として、**Oracle Cloud Infrastructure (OCI) Always Free**枠を利用する。
本ドキュメントでは、インスタンスの作成からネットワーク設定、本番サーバーの基本セットアップまでの手順を定義する。

---

# 2. 前提条件
- Oracle Cloud アカウントが作成済みであること。
- ドメインが取得済みであり、OCIインスタンスのパブリックIPアドレスにDNS（Aレコード）が紐付けられていること。

---

# 3. 構築手順

## Step 1: インスタンスの作成 (OCI Console)
1. OCI コンソールにログイン後、[コンピュート] -> [インスタンス] -> [インスタンスの作成] を選択。
2. 以下の設定値でインスタンスを作成する。
   - **名前**: `presence-board-prod`
   - **イメージ**: `Ubuntu 22.04 LTS` または `Ubuntu 24.04 LTS` (Canonical Ubuntu)
   - **シェイプ**: `VM.Standard.A1.Flex` (ARM Ampere) を推奨。
     - OCI Free Tier枠内で **4 OCPU / 24 GB メモリ** まで無償利用可能。
     - （もしARMの空きがない場合は、標準の `VM.Standard.E2.1.Micro` AMD 1OCPU/1GB でも動作可能）
   - **ネットワーク**: 新規仮想クラウド・ネットワーク (VCN) およびパブリック・サブネットを作成。
   - **SSHキー**: ローカルのSSH公開鍵（作成した `id_ed25519.pub`）をアップロード。
3. [作成] をクリックし、割り当てられた **パブリックIPアドレス** を控える。

## Step 2: ネットワーク設定 (セキュリティ・リスト)
インターネットからウェブアクセス（HTTP/HTTPS）を受け入れるため、仮想クラウド・ネットワーク (VCN) のセキュリティ・リストに入力（イングレス）ルールを追加する。

1. インスタンス詳細画面の [プライマリVNIC] -> [サブネット] -> [セキュリティ・リスト] を開く。
2. **イングレス・ルールの追加** をクリックし、以下の2つのルールを追加する。
   - **ルール1 (HTTP)**:
     - ソースCIDR: `0.0.0.0/0`
     - IPプロトコル: `TCP`
     - 宛先ポート範囲: `80`
   - **ルール2 (HTTPS)**:
     - ソースCIDR: `0.0.0.0/0`
     - IPプロトコル: `TCP`
     - 宛先ポート範囲: `443`

---

# 4. サーバーの基本セットアップ

SSH接続確認後、サーバー内で以下のセットアップを実行する。

## 4.1 パッケージの更新
```bash
sudo apt update && sudo apt upgrade -y
```

## 4.2 OSファイアウォール (iptables) の開放
Ubuntuではデフォルトで特定のポート以外拒否されているため、OSレベルのファイアウォールも開放する。
```bash
sudo iptables -I INPUT 6 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## 4.3 Docker / Docker Compose のインストール
Docker公式のスクリプトを利用してインストールする。
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```
再ログイン後、`docker compose` コマンドが有効になっていることを確認する。

---

# 5. デプロイ方針
本番デプロイは以下の順序でコンテナを稼働させる（詳細は `13_デプロイ手順.md` 参照）。
1. リポジトリを本番サーバーへクローン。
2. NginxコンテナとLet's Encrypt（Certbot）を連携させ、TLS証明書を適用。
3. `docker-compose.prod.yml`（Gunicorn + Nginx + PostgreSQL）を用いて本番コンテナ群を起動。
