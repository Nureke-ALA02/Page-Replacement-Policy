from collections import deque
from .base import Policy

class FIFO(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._queue: deque = deque()

    def _on_hit(self, page: int) -> None:
        pass

    def _on_miss_with_room(self, page: int) -> None:
        self._queue.append(page)

    def _evict(self, incoming: int) -> int:
        victim = self._queue.popleft()
        self._queue.append(incoming)
        return victim
