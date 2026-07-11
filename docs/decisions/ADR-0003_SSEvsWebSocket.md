# ADR-0003: リアルタイム更新にSSEを採用（WebSocketは不採用）

## ステータス
承認済み

## コンテキスト
一覧画面の状態変更を全ユーザーにリアルタイム反映する必要がある。約100名規模での利用を想定。

## 決定
Server-Sent Events (SSE) を採用する。WebSocketは採用しない。

## 理由
- サーバ→クライアントの一方向通知のみで要件を満たせる（クライアントからのリアルタイム双方向通信は不要）
- 100人規模であればSSEで十分にスケールし、実装・運用がWebSocketより単純
- Django標準の`StreamingHttpResponse`で実現でき、`django-channels`等の追加依存を避けられる（`01_プロジェクト概要.md`のDjango標準優先方針に合致）

## 代替案と却下理由
- WebSocket（django-channels等）: 双方向通信は不要なオーバースペック。ASGI化・Redis等の追加インフラが必要になり、Oracle Cloud Free枠上での運用が複雑化する

## 影響・リスク
- Gunicornのマルチワーカー構成時、プロセス間でのSSEイベント共有に課題が残る（`06_API・SSE設計.md` 4章のTODO参照）
- ワーカー数を1に固定するか、将来的に軽量なブローカー（Redis等）の追加導入を検討する必要がある
