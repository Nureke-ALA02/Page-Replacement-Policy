"""
FIFO page replacement.

The oldest-loaded page is evicted, regardless of how often or how recently
it was used. Notable property: FIFO is *not* a stack algorithm, so it can
exhibit Belady's anomaly (more frames -> more faults).
"""

from collections import deque
from .base import Policy


class FIFO(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._queue: deque = deque()  # left = oldest, right = newest

    def _on_hit(self, page: int) -> None:
        # FIFO does nothing on a hit — that's what makes it "dumb" but also
        # what makes Belady's anomaly possible.
        pass

    def _on_miss_with_room(self, page: int) -> None:
        self._queue.append(page)

    def _evict(self, incoming: int) -> int:
        victim = self._queue.popleft()
        self._queue.append(incoming)
        return victim
