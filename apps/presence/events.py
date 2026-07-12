import abc
import queue
import threading
import os
import json
import logging

logger = logging.getLogger(__name__)

# イベント種別定義の整理 (TASK-011)
EVENT_WELCOME = "welcome"
EVENT_HEARTBEAT = "heartbeat"
EVENT_PRESENCE_UPDATED = "presence_updated"

VALID_EVENTS = {
    EVENT_WELCOME,
    EVENT_HEARTBEAT,
    EVENT_PRESENCE_UPDATED
}


class Subscription(abc.ABC):
    """
    イベントを受信するための抽象サブスクリプションクラス。
    """
    @abc.abstractmethod
    def get(self, timeout: float | None = None) -> tuple[str, dict]:
        """
        次のイベントを (event_name, data) のタプルで取得する。
        """
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """
        購読を解除する。
        """
        pass


class MemorySubscription(Subscription):
    """
    MemoryEventPublisher 用のサブスクリプション実装。
    """
    def __init__(self, publisher: 'MemoryEventPublisher'):
        self.publisher = publisher
        self.queue: queue.Queue[tuple[str, dict]] = queue.Queue(maxsize=100)
        self.publisher.register_q(self.queue)

    def get(self, timeout: float | None = None) -> tuple[str, dict]:
        return self.queue.get(timeout=timeout)

    def close(self) -> None:
        self.publisher.unregister_q(self.queue)


class RedisSubscription(Subscription):
    """
    RedisEventPublisher 用のサブスクリプション実装。
    """
    def __init__(self, channel_name: str, redis_url: str):
        self.channel_name = channel_name
        self.redis_url = redis_url
        import redis  # type: ignore[import-not-found]
        self.r = redis.from_url(redis_url)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(channel_name)

    def get(self, timeout: float | None = None) -> tuple[str, dict]:
        import time
        start_time = time.time()
        while True:
            try:
                # redisのpubsub接続から1メッセージを読み取る
                msg = self.pubsub.get_message(ignore_subscribe_messages=True, timeout=timeout)
                if msg:
                    payload = json.loads(msg['data'].decode('utf-8') if isinstance(msg['data'], bytes) else msg['data'])
                    return payload['event'], payload['data']
            except Exception as e:
                logger.error(f"Error reading from Redis subscription: {e}")
                raise queue.Empty() from e

            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise queue.Empty()
                time.sleep(0.1)
            else:
                time.sleep(0.1)

    def close(self) -> None:
        try:
            self.pubsub.unsubscribe()
            self.pubsub.close()
        except Exception as e:
            logger.warning(f"Error closing Redis pubsub subscription: {e}")


class EventPublisher(abc.ABC):
    """
    イベント配信を行う抽象ベースクラス（将来の Redis 移行等を見据えた共通インターフェース）。
    """
    @abc.abstractmethod
    def broadcast(self, event_name: str, data: dict) -> None:
        pass

    @abc.abstractmethod
    def subscribe(self) -> Subscription:
        pass


class MemoryEventPublisher(EventPublisher):
    """
    メモリ上で動作するスレッドセーフなプロセス内イベントブロードキャスト。
    """
    def __init__(self):
        self.listeners = []
        self.lock = threading.Lock()

    def register(self):
        """
        後方互換性テストおよびレガシーコードのために残したメソッド。
        """
        q = queue.Queue(maxsize=100)
        self.register_q(q)
        return q

    def unregister(self, q):
        """
        後方互換性テストおよびレガシーコードのために残したメソッド。
        """
        self.unregister_q(q)

    def register_q(self, q):
        with self.lock:
            self.listeners.append(q)

    def unregister_q(self, q):
        with self.lock:
            if q in self.listeners:
                self.listeners.remove(q)

    def broadcast(self, event_name: str, data: dict) -> None:
        if event_name not in VALID_EVENTS:
            raise ValueError(f"Invalid event name: {event_name}. Must be one of {VALID_EVENTS}")

        with self.lock:
            for q in self.listeners:
                try:
                    q.put_nowait((event_name, data))
                except queue.Full:
                    # キューが満杯の場合は古いイベントを捨てるなどの対応を考慮しつつ、ここでは無視して進む
                    pass

    def subscribe(self) -> Subscription:
        return MemorySubscription(self)


class RedisEventPublisher(EventPublisher):
    """
    将来の Redis Pub/Sub 導入時に用いるマルチプロセス対応用実装。
    """
    def __init__(self, channel_name: str = 'presence_events', redis_url: str | None = None):
        self.channel_name = channel_name
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    def broadcast(self, event_name: str, data: dict) -> None:
        if event_name not in VALID_EVENTS:
            raise ValueError(f"Invalid event name: {event_name}. Must be one of {VALID_EVENTS}")

        try:
            import redis  # type: ignore[import-not-found]
            r = redis.from_url(self.redis_url)
            payload = json.dumps({"event": event_name, "data": data})
            r.publish(self.channel_name, payload)
        except ImportError:
            logger.warning("redis library is not installed. Failed to broadcast to Redis.")
        except Exception as e:
            logger.error(f"Redis broadcast error: {e}")

    def subscribe(self) -> Subscription:
        try:
            import redis  # type: ignore[import-not-found]  # noqa: F401
            return RedisSubscription(self.channel_name, self.redis_url)
        except ImportError:
            logger.error("redis library is not installed. Falling back to memory-based subscription stub.")
            raise RuntimeError("redis package is required for RedisEventPublisher subscription")


# 環境変数または Django 設定からパブリッシャーを切り替え
REDIS_URL = os.environ.get('REDIS_URL')

event_publisher: EventPublisher

if REDIS_URL:
    try:
        import redis  # type: ignore[import-not-found]  # noqa: F401
        event_publisher = RedisEventPublisher(redis_url=REDIS_URL)
        logger.info("Using RedisEventPublisher for SSE event publishing.")
    except ImportError:
        logger.warning("REDIS_URL is configured but 'redis' library is not installed. Falling back to MemoryEventPublisher.")
        event_publisher = MemoryEventPublisher()
else:
    event_publisher = MemoryEventPublisher()

