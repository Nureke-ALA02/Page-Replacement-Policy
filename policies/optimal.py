from typing import Dict, List
from .base import OracleNeedsTrace


class OPT(OracleNeedsTrace):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._next_uses: Dict[int, List[int]] = {}
        self._cursor: Dict[int, int] = {}

    def set_trace(self, trace):
        super().set_trace(trace)
        self._next_uses.clear()
        self._cursor.clear()
        for i, p in enumerate(trace):
            self._next_uses.setdefault(p, []).append(i)
        for p in self._next_uses:
            self._cursor[p] = 0

    def _advance_cursor(self, page: int) -> None:
        positions = self._next_uses.get(page, ())
        c = self._cursor.get(page, 0)
        while c < len(positions) and positions[c] <= self._pos:
            c += 1
        self._cursor[page] = c

    def _next_use_distance(self, page: int) -> int:
        self._advance_cursor(page)
        positions = self._next_uses.get(page, ())
        c = self._cursor.get(page, 0)
        if c >= len(positions):
            return float("inf")
        return positions[c]

    # Policy hooks

    def _on_hit(self, page: int) -> None:
        pass
    def _on_miss_with_room(self, page: int) -> None:
        pass
    def _evict(self, incoming: int) -> int:
        victim = None
        best_dist = -1
        for p in self.resident:
            d = self._next_use_distance(p)
            if d > best_dist:
                best_dist = d
                victim = p
                if d == float("inf"):
                    break
        assert victim is not None
        return victim
