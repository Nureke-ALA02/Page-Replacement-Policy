"""
Synthetic trace generators.

These are the standard workloads used in the page-replacement literature
(OSTEP, Silberschatz, Tanenbaum). Each function returns a list of ints.

Generators:
    uniform_random  — every page equally likely (worst case for any policy)
    zipf            — power-law popularity (realistic for many workloads)
    looping         — 1,2,...,N,1,2,...,N,... (LRU's worst case)
    working_set     — slowly drifting hot set (realistic OS workload)
    sequential_scan — linear scan over an array
    belady_anomaly  — the classic 12-reference sequence where FIFO faults
                      *more* with 4 frames than with 3

All generators take an optional `seed` for reproducibility.
"""

from __future__ import annotations
import math
import random
from typing import List


def uniform_random(n_refs: int, n_pages: int, seed: int = 0) -> List[int]:
    rng = random.Random(seed)
    return [rng.randrange(n_pages) for _ in range(n_refs)]


def zipf(n_refs: int, n_pages: int, alpha: float = 1.0, seed: int = 0) -> List[int]:
    """Zipfian popularity: probability(rank k) ∝ 1 / k^alpha.

    alpha = 0 → uniform; alpha = 1 → classic Zipf; alpha = 2 → very skewed.

    We build a CDF over page ranks, then sample. Pages are labeled 0..n_pages-1
    with 0 being the most popular.
    """
    rng = random.Random(seed)
    weights = [1.0 / ((k + 1) ** alpha) for k in range(n_pages)]
    total = sum(weights)
    cdf = []
    acc = 0.0
    for w in weights:
        acc += w / total
        cdf.append(acc)
    out = []
    for _ in range(n_refs):
        r = rng.random()
        # Binary search for the first cdf entry >= r.
        lo, hi = 0, n_pages - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cdf[mid] < r:
                lo = mid + 1
            else:
                hi = mid
        out.append(lo)
    return out


def looping(n_refs: int, n_pages: int) -> List[int]:
    """1,2,...,N,1,2,...,N,...

    Catastrophic for LRU when capacity = n_pages - 1: every access misses.
    """
    return [i % n_pages for i in range(n_refs)]


def working_set(
    n_refs: int,
    n_pages: int,
    ws_size: int,
    shift_every: int = 1000,
    shift_by: int = 1,
    seed: int = 0,
) -> List[int]:
    """Hot working set of size `ws_size` that drifts every `shift_every` refs.

    Models a program that operates on a working set, then gradually moves
    on (e.g., loop nest moving through a large array).
    """
    rng = random.Random(seed)
    out = []
    base = 0
    for i in range(n_refs):
        if i > 0 and i % shift_every == 0:
            base = (base + shift_by) % max(1, n_pages - ws_size + 1)
        out.append(base + rng.randrange(ws_size))
    return out


def sequential_scan(n_refs: int, n_pages: int) -> List[int]:
    """Single pass through pages 0..n_pages-1, repeated if n_refs > n_pages."""
    return [i % n_pages for i in range(n_refs)]


def belady_anomaly() -> List[int]:
    """The textbook sequence demonstrating Belady's anomaly for FIFO.

    With 3 frames FIFO produces 9 faults.
    With 4 frames FIFO produces 10 faults — *more* memory, *more* faults.
    See Belady, Nelson & Shedler (1969).
    """
    return [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
