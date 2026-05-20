"""
LRU page replacement.

Evicts the page that was used the longest time ago. LRU is a stack
algorithm — its set of resident pages with k+1 frames is a superset of the
set with k frames — so LRU cannot exhibit Belady's anomaly.

Implementation uses OrderedDict for O(1) move-to-end and O(1) popitem(last=False).
A doubly-linked list + hashmap would also work; OrderedDict is the same
data structure internally and is the standard Python idiom.
"""

from collections import OrderedDict
from .base import Policy


class LRU(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        # Key = page, value = unused. We only need the ordering.
        self._od: OrderedDict = OrderedDict()

    def _on_hit(self, page: int) -> None:
        # Move to "most recently used" end.
        self._od.move_to_end(page, last=True)

    def _on_miss_with_room(self, page: int) -> None:
        self._od[page] = None  # value is irrelevant

    def _evict(self, incoming: int) -> int:
        # popitem(last=False) removes the LRU end.
        victim, _ = self._od.popitem(last=False)
        self._od[incoming] = None
        return victim
