import abc
import queue
import threading

class EventPublisher(abc.ABC):
    """
    イベント配信を行う抽象ベースクラス（将来の Redis 移行等を見据えた共通インターフェース）。
    """
    @abc.abstractmethod
    def broadcast(self, event_name: str, data: dict) -> None:
        pass


class MemoryEventPublisher(EventPublisher):
    """
    メモリ上で動作するスレッドセーフなプロセス内イベントブロードキャスト。
    """
    def __init__(self):
        self.listeners = []
        self.lock = threading.Lock()

    def register(self):
        q = queue.Queue(maxsize=100)
        with self.lock:
            self.listeners.append(q)
        return q

    def unregister(self, q):
        with self.lock:
            if q in self.listeners:
                self.listeners.remove(q)

    def broadcast(self, event_name: str, data: dict) -> None:
        with self.lock:
            for q in self.listeners:
                try:
                    q.put_nowait((event_name, data))
                except queue.Full:
                    # キューが満杯の場合は古いイベントを捨てるなどの対応を考慮しつつ、ここでは無視して進む
                    pass


class RedisEventPublisher(EventPublisher):
    """
    将来の Redis Pub/Sub 導入時に用いるマルチプロセス対応用実装スタブ。
    """
    def broadcast(self, event_name: str, data: dict) -> None:
        # TODO: Redis クライアントを取得し、publish を実行する
        # e.g. redis_client.publish('presence_channel', json.dumps({event_name: data}))
        pass


# デフォルトのパブリッシャーとして MemoryEventPublisher をセット
event_publisher = MemoryEventPublisher()
