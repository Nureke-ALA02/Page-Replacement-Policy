from collections import OrderedDict
from .base import Policy


class LRU(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._od: OrderedDict = OrderedDict()

    def _on_hit(self, page: int) -> None:
        self._od.move_to_end(page, last=True)

    def _on_miss_with_room(self, page: int) -> None:
        self._od[page] = None

    def _evict(self, incoming: int) -> int:
        victim, _ = self._od.popitem(last=False)
        self._od[incoming] = None
        return victim