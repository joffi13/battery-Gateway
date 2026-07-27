from collections import deque

from core.event import Event


class EventBus:

    def __init__(self):
        self._queue = deque()

    def publish(self, event: Event):
        self._queue.append(event)

    def has_events(self) -> bool:
        return len(self._queue) > 0

    def get(self):
        if self._queue:
            return self._queue.popleft()
        return None

    def clear(self):
        self._queue.clear()

    def count(self) -> int:
        return len(self._queue)

    def __repr__(self):
        return f"<EventBus events={len(self._queue)}>"
