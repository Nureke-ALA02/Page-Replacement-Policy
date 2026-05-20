"""
Base interface for page replacement policies.

Every policy implements `access(page)` which returns True on hit, False on miss
(page fault). The policy itself is responsible for evicting a victim when the
buffer is full.

We deliberately keep this interface tiny: the simulator does not care about
internal state. This lets us mix-and-match policies in experiments.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class Policy(ABC):
    """Abstract base class for a page replacement policy.

    Parameters
    ----------
    capacity : int
        Number of physical frames available. Must be >= 1.

    Notes
    -----
    Subclasses must implement `_on_hit`, `_on_miss_with_room`, and `_evict`.
    The public `access` method takes care of bookkeeping (counters) and
    dispatches to those hooks. This template-method design keeps subclasses
    short and free of duplicated counter logic.
    """

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self.capacity = capacity
        self.resident: set = set()   # which pages are currently in memory
        self.hits = 0
        self.faults = 0              # also called "misses"

    # ---- Public API ------------------------------------------------------

    def access(self, page: int) -> bool:
        """Process one memory reference.

        Returns True on a hit, False on a page fault.
        """
        if page in self.resident:
            self.hits += 1
            self._on_hit(page)
            return True

        # Page fault path
        self.faults += 1
        if len(self.resident) < self.capacity:
            self._on_miss_with_room(page)
            self.resident.add(page)
        else:
            victim = self._evict(page)
            if victim not in self.resident:
                raise RuntimeError(
                    f"{self.name} evicted {victim} but it is not resident"
                )
            self.resident.remove(victim)
            self.resident.add(page)
        return False

    def run(self, trace: List[int]) -> None:
        """Convenience: replay a whole trace."""
        for p in trace:
            self.access(p)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def total_refs(self) -> int:
        return self.hits + self.faults

    @property
    def hit_rate(self) -> float:
        return self.hits / self.total_refs if self.total_refs else 0.0

    @property
    def fault_rate(self) -> float:
        return self.faults / self.total_refs if self.total_refs else 0.0

    # ---- Subclass hooks --------------------------------------------------

    @abstractmethod
    def _on_hit(self, page: int) -> None:
        """Update internal metadata on a hit (e.g., move-to-front for LRU)."""

    @abstractmethod
    def _on_miss_with_room(self, page: int) -> None:
        """Update internal metadata when we add a page and have room."""

    @abstractmethod
    def _evict(self, incoming: int) -> int:
        """Choose a victim page to evict. Must return a page currently
        resident. `incoming` is provided in case the policy wants to peek
        (e.g., OPT uses the future stream, not `incoming` alone).
        """


class OracleNeedsTrace(Policy):
    """Mixin for policies (like Belady's OPT) that need to see the future.

    Such policies receive the full trace up front and a pointer to the
    current position. The simulator must call `set_trace` before `access`.
    """

    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._trace: Optional[List[int]] = None
        self._pos = 0

    def set_trace(self, trace: List[int]) -> None:
        self._trace = trace
        self._pos = 0

    def access(self, page: int) -> bool:  # type: ignore[override]
        if self._trace is None:
            raise RuntimeError(
                f"{self.name} requires set_trace() before access()"
            )
        result = super().access(page)
        self._pos += 1
        return result
