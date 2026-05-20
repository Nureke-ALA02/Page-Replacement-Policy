"""
Aging page replacement.

Each page has an N-bit (default 8) "age" counter. On every clock tick:
    age = (age >> 1) | (ref_bit << (N-1))
    ref_bit = 0

This way, the high bit reflects recent access, the next bit reflects
access in the previous tick, and so on. The page with the lowest age
counter is the one least recently / least frequently used over the window
of N ticks. The policy combines LRU's recency awareness with LFU's
frequency tolerance, at very low cost — a single integer per page.

In real OS we'd tick on a hardware timer; in simulation we tick every
`tick_interval` references (default 1, but configurable to compare
behaviors).

This is the classic textbook "Aging" algorithm from Carr & Hennessy and
also appears in Silberschatz/Galvin/Gagne and OSTEP.
"""

from .base import Policy


class Aging(Policy):
    def __init__(self, capacity: int, bits: int = 8, tick_interval: int = 1):
        super().__init__(capacity)
        self.bits = bits
        self.tick_interval = tick_interval
        self._age: dict = {}          # page -> age counter
        self._ref: dict = {}          # page -> reference bit (0/1)
        self._refs_since_tick = 0

    def _maybe_tick(self) -> None:
        self._refs_since_tick += 1
        if self._refs_since_tick >= self.tick_interval:
            self._refs_since_tick = 0
            mask = (1 << self.bits) - 1
            high = 1 << (self.bits - 1)
            for p in self.resident:
                a = self._age.get(p, 0)
                a = ((a >> 1) | (self._ref.get(p, 0) * high)) & mask
                self._age[p] = a
                self._ref[p] = 0

    def access(self, page: int) -> bool:  # type: ignore[override]
        # We override access() so we can tick *before* updating ref bit
        # for the incoming page — this matches textbook semantics.
        self._maybe_tick()
        return super().access(page)

    def _on_hit(self, page: int) -> None:
        self._ref[page] = 1

    def _on_miss_with_room(self, page: int) -> None:
        self._age[page] = 0
        self._ref[page] = 1

    def _evict(self, incoming: int) -> int:
        # Pick lowest age; tiebreak by smallest page id for determinism.
        victim = min(self.resident, key=lambda p: (self._age[p], p))
        del self._age[victim]
        del self._ref[victim]
        self._age[incoming] = 0
        self._ref[incoming] = 1
        return victim
