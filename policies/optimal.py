"""
Belady's Optimal (OPT / MIN / Belady's algorithm).

On a fault, evict the page whose *next* use is furthest in the future
(or never). Belady proved in 1966 that this is optimal — no online or
offline policy can produce fewer page faults.

OPT is offline: it needs the entire trace up front. We use it as a
lower-bound oracle to evaluate online policies. The "competitive ratio"
of LRU is `faults_LRU / faults_OPT` and is a classical bound.

Implementation notes:
- For each page, we precompute a list of positions where it occurs.
- During simulation we advance a per-page pointer; the "next use distance"
  is the next position >= current.
- A heap keyed by next-use position would speed eviction, but for the
  trace sizes we deal with, a linear scan over `resident` is fine and
  much simpler to reason about.
"""

from typing import Dict, List
from .base import OracleNeedsTrace


class OPT(OracleNeedsTrace):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._next_uses: Dict[int, List[int]] = {}
        # Pointer into _next_uses[page]: index of the first occurrence
        # at position >= self._pos.
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
        """Move the cursor for `page` to the first occurrence > self._pos."""
        positions = self._next_uses.get(page, ())
        c = self._cursor.get(page, 0)
        while c < len(positions) and positions[c] <= self._pos:
            c += 1
        self._cursor[page] = c

    def _next_use_distance(self, page: int) -> int:
        """How far in the future is `page` next used? Returns a huge
        sentinel if it is never used again."""
        self._advance_cursor(page)
        positions = self._next_uses.get(page, ())
        c = self._cursor.get(page, 0)
        if c >= len(positions):
            return float("inf")  # "never again" — perfect victim
        return positions[c]

    # ---- Policy hooks ----------------------------------------------------

    def _on_hit(self, page: int) -> None:
        pass  # nothing to do; cursors are advanced lazily on demand

    def _on_miss_with_room(self, page: int) -> None:
        pass

    def _evict(self, incoming: int) -> int:
        # Pick the resident page with the largest next-use distance.
        # Ties: arbitrary (we take whichever comes first in iteration).
        victim = None
        best_dist = -1
        for p in self.resident:
            d = self._next_use_distance(p)
            if d > best_dist:
                best_dist = d
                victim = p
                if d == float("inf"):
                    break  # can't do better than "never used again"
        assert victim is not None
        return victim
