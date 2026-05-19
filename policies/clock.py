"""
Clock (a.k.a. Second-Chance) page replacement.

Each frame has a reference bit. Frames are arranged in a circular buffer
with a "hand" pointer. To evict:
  - if the page under the hand has ref=0, evict it; advance hand
  - else clear ref bit, advance hand, repeat

This approximates LRU at much lower bookkeeping cost: no per-access work
to maintain a recency list — only a single bit flip on hit. Real OSes use
variants of Clock (Linux's PFRA, FreeBSD's "queue scan", etc.) because
maintaining a true LRU list under heavy load is too expensive.

We store the buffer as a fixed-size list of (page, ref_bit) slots so the
hand pointer is just an integer modulo capacity.
"""

from .base import Policy


class Clock(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._slots: list = []          # list of [page, ref_bit]; len <= capacity
        self._index: dict = {}          # page -> index in _slots, for O(1) hit
        self._hand = 0                  # current hand position

    def _on_hit(self, page: int) -> None:
        i = self._index[page]
        self._slots[i][1] = 1           # set reference bit

    def _on_miss_with_room(self, page: int) -> None:
        # We have room — just append. Don't move the hand.
        self._slots.append([page, 1])
        self._index[page] = len(self._slots) - 1

    def _evict(self, incoming: int) -> int:
        # Spin until we find ref=0. Each pass clears ref bits we see.
        while True:
            slot = self._slots[self._hand]
            page, ref = slot
            if ref == 0:
                # Evict this slot; place incoming here; advance hand past it.
                del self._index[page]
                self._slots[self._hand] = [incoming, 1]
                self._index[incoming] = self._hand
                victim = page
                self._hand = (self._hand + 1) % self.capacity
                return victim
            else:
                slot[1] = 0
                self._hand = (self._hand + 1) % self.capacity
