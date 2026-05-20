"""
ARC: Adaptive Replacement Cache (Megiddo & Modha, FAST '03).

ARC partitions the cache of size c into two adaptive halves:
  T1 — pages seen exactly once recently (recency)
  T2 — pages seen at least twice recently (frequency)
Plus two "ghost" lists (only page IDs, no data):
  B1 — pages recently evicted from T1
  B2 — pages recently evicted from T2

Invariants:
  |T1| + |T2| <= c
  |T1| + |B1| <= c
  |T2| + |B2| <= 2c
  |T1| + |T2| + |B1| + |B2| <= 2c

A target parameter p (0 <= p <= c) governs how much of the cache T1 may
own. p adapts: a hit in B1 increases p (recency is winning), a hit in B2
decreases p (frequency is winning). This is what makes ARC "adaptive".

Reference algorithm: Figure 4 of the FAST '03 paper. The four cases of
`access` and the `replace` subroutine below mirror it directly.

Implementation note: each list is an OrderedDict so we can do O(1)
move-to-MRU-end, O(1) pop-LRU-end, O(1) membership.
"""

from collections import OrderedDict
from .base import Policy


class ARC(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self.c = capacity
        self.p = 0                            # target size of T1
        self.T1: OrderedDict = OrderedDict()  # recency
        self.T2: OrderedDict = OrderedDict()  # frequency
        self.B1: OrderedDict = OrderedDict()  # ghost recency
        self.B2: OrderedDict = OrderedDict()  # ghost frequency

    # The base class tracks `resident`, `hits`, `faults` via `access()`.
    # ARC's "resident" is T1 ∪ T2. We override `access` entirely because
    # the base hooks (_on_hit / _evict) don't map cleanly to ARC's four
    # cases (hit in T1∪T2, hit in B1, hit in B2, miss).

    def access(self, page: int) -> bool:  # type: ignore[override]
        # Case I: cache hit (T1 or T2)
        if page in self.T1:
            del self.T1[page]
            self.T2[page] = None   # promote to T2 (MRU end)
            self.hits += 1
            return True
        if page in self.T2:
            self.T2.move_to_end(page, last=True)
            self.hits += 1
            return True

        # Miss
        self.faults += 1

        # Case II: hit in B1 ghost list
        if page in self.B1:
            delta = max(1, len(self.B2) // max(1, len(self.B1)))
            self.p = min(self.c, self.p + delta)
            self._replace(page)
            del self.B1[page]
            self.T2[page] = None
            self.resident = set(self.T1) | set(self.T2)
            return False

        # Case III: hit in B2 ghost list
        if page in self.B2:
            delta = max(1, len(self.B1) // max(1, len(self.B2)))
            self.p = max(0, self.p - delta)
            self._replace(page)
            del self.B2[page]
            self.T2[page] = None
            self.resident = set(self.T1) | set(self.T2)
            return False

        # Case IV: page not in cache, not in B1, not in B2.
        # The paper has two sub-cases controlling how the ghost lists
        # are kept bounded by `c` and `2c`.
        L1_size = len(self.T1) + len(self.B1)
        L2_size = len(self.T2) + len(self.B2)
        if L1_size == self.c:
            if len(self.T1) < self.c:
                # Drop LRU of B1, then replace.
                self.B1.popitem(last=False)
                self._replace(page)
            else:
                # B1 is empty; T1 has all c entries. Evict LRU of T1
                # outright (no ghost — it'd just immediately be dropped).
                evicted, _ = self.T1.popitem(last=False)
                # Do not add to B1 — there's no room. (Paper handles this
                # via the L1 == c branch falling through.)
                # Actually paper says: delete LRU page in T1 (also remove
                # it from cache). No ghosting in this branch.
                _ = evicted
        elif L1_size < self.c and (L1_size + L2_size) >= self.c:
            if (L1_size + L2_size) == 2 * self.c:
                self.B2.popitem(last=False)
            self._replace(page)

        self.T1[page] = None
        self.resident = set(self.T1) | set(self.T2)
        return False

    # ---------------------------------------------------------------------

    def _replace(self, incoming: int) -> None:
        """REPLACE subroutine from the paper.

        Evict one page from T1 or T2 (and ghost it into B1 or B2) so that
        we maintain |T1| + |T2| <= c.
        """
        if self.T1 and (
            len(self.T1) > self.p
            or (incoming in self.B2 and len(self.T1) == self.p)
        ):
            # Move LRU of T1 to MRU of B1
            evicted, _ = self.T1.popitem(last=False)
            self.B1[evicted] = None
        else:
            # Move LRU of T2 to MRU of B2
            evicted, _ = self.T2.popitem(last=False)
            self.B2[evicted] = None

    # ARC overrides access(), so the base hooks aren't called. We still
    # provide trivial implementations so the abstract class is happy.
    def _on_hit(self, page: int) -> None:
        pass

    def _on_miss_with_room(self, page: int) -> None:
        pass

    def _evict(self, incoming: int) -> int:
        # Unused — ARC's eviction happens inside `_replace`.
        raise NotImplementedError

    # Diagnostic — useful in unit tests and slides.
    def state(self) -> dict:
        return {
            "p": self.p,
            "T1": list(self.T1),
            "T2": list(self.T2),
            "B1": list(self.B1),
            "B2": list(self.B2),
        }
