import queue
import threading

class EventBus:
    """
    スレッドセーフなプロセス内イベントブロードキャスト管理クラス。
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

    def broadcast(self, event_name, data):
        with self.lock:
            for q in self.listeners:
                try:
                    q.put_nowait((event_name, data))
                except queue.Full:
                    # キューが満杯の場合は無視して進む（または古いアイテムを捨てる）
                    pass

event_bus = EventBus()
