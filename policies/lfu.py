"""
LFU page replacement.

Evicts the page with the lowest reference count. Ties are broken by
oldest-loaded (FIFO) to make behavior deterministic.

Pure LFU has a well-known weakness: a page accessed many times during
program startup but never afterwards stays resident forever, because its
count is huge. "Aging" (see aging.py) fixes this by periodically halving
counts. We keep this implementation as the textbook pure LFU for
comparison.

Implementation is O(capacity) per eviction (linear scan). For real systems
you'd use a min-heap or the O(1) LFU scheme of Shi et al., but our
capacities are small (typically <= a few thousand frames) so a linear
scan is fine and much clearer.
"""

from .base import Policy


class LFU(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._count: dict = {}          # page -> access count
        self._load_order: dict = {}     # page -> load timestamp (tiebreak)
        self._tick = 0

    def _on_hit(self, page: int) -> None:
        self._count[page] = self._count.get(page, 0) + 1

    def _on_miss_with_room(self, page: int) -> None:
        self._count[page] = 1
        self._tick += 1
        self._load_order[page] = self._tick

    def _evict(self, incoming: int) -> int:
        # Find the resident page with smallest count; tiebreak: smallest
        # load_order (oldest in memory).
        victim = min(
            self.resident,
            key=lambda p: (self._count[p], self._load_order[p]),
        )
        del self._count[victim]
        del self._load_order[victim]
        self._count[incoming] = 1
        self._tick += 1
        self._load_order[incoming] = self._tick
        return victim
