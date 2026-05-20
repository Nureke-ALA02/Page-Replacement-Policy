"""Cross-policy invariants.

These tests run *every* registered policy through a small workload and
verify universal invariants:
  - |resident| <= capacity at all times.
  - hits + faults == total references.
  - Every resident page was at some point requested.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
import pytest
from policies import REGISTRY, OracleNeedsTrace


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_capacity_invariant(name):
    cls = REGISTRY[name]
    rng = random.Random(42)
    trace = [rng.randrange(20) for _ in range(500)]
    p = cls(5)
    if isinstance(p, OracleNeedsTrace):
        p.set_trace(trace)
    for x in trace:
        p.access(x)
        assert len(p.resident) <= 5


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_counters_consistent(name):
    cls = REGISTRY[name]
    rng = random.Random(1)
    trace = [rng.randrange(10) for _ in range(300)]
    p = cls(4)
    if isinstance(p, OracleNeedsTrace):
        p.set_trace(trace)
    p.run(trace)
    assert p.hits + p.faults == len(trace)


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_residents_were_referenced(name):
    cls = REGISTRY[name]
    trace = [1, 2, 3, 4, 5, 1, 2, 6]
    p = cls(3)
    if isinstance(p, OracleNeedsTrace):
        p.set_trace(trace)
    p.run(trace)
    assert p.resident.issubset(set(trace))
