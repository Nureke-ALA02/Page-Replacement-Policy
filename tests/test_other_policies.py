import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
from policies import Clock, LFU, Aging, ARC

def test_clock_basic():
    p = Clock(3)
    p.run([1, 2, 3])
    assert p.faults == 3 and p.resident == {1, 2, 3}

    p.access(1)
    p.access(2)
    p.access(3)
    p.access(4)
    assert 4 in p.resident
    assert len(p.resident) == 3


def test_clock_no_eviction_when_room():
    p = Clock(5)
    for x in [1, 2, 3]:
        p.access(x)
    assert p.resident == {1, 2, 3}

def test_lfu_evicts_least_frequent():
    p = LFU(3)
    p.run([1, 1, 1, 2, 2, 3])

    p.access(4)
    assert 3 not in p.resident
    assert 1 in p.resident and 2 in p.resident and 4 in p.resident


def test_lfu_tiebreak_by_load_order():
    """When counts tie, evict the one loaded earliest."""
    p = LFU(3)
    p.run([1, 2, 3]) 
    p.access(4)       
    assert 1 not in p.resident

def test_aging_basic():
    p = Aging(3, bits=8, tick_interval=1)
    p.run([1, 2, 3])
    assert p.faults == 3
    p.access(1)
    p.access(1)
    p.access(4)
    assert 1 in p.resident
    assert 4 in p.resident


def test_aging_capacity_invariant():
    """Resident set never exceeds capacity, regardless of trace."""
    rng = random.Random(0)
    trace = [rng.randrange(50) for _ in range(2000)]
    p = Aging(8)
    p.run(trace)
    assert len(p.resident) <= p.capacity


def test_arc_basic():
    p = ARC(3)
    p.run([1, 2, 3])
    assert p.faults == 3 and p.resident == {1, 2, 3}


def test_arc_invariants_after_random_workload():
    """Check ARC's structural invariants throughout a stress run.

    |T1| + |T2| <= c, |T1| + |B1| <= c, |T2| + |B2| <= 2c,
    |T1| + |T2| + |B1| + |B2| <= 2c, 0 <= p <= c.
    """
    rng = random.Random(123)
    trace = [rng.randrange(40) for _ in range(2000)]
    c = 8
    p = ARC(c)
    for x in trace:
        p.access(x)
        st = p.state()
        assert len(st["T1"]) + len(st["T2"]) <= c
        assert len(st["T1"]) + len(st["B1"]) <= c
        assert len(st["T2"]) + len(st["B2"]) <= 2 * c
        assert (len(st["T1"]) + len(st["T2"]) +
                len(st["B1"]) + len(st["B2"])) <= 2 * c
        assert 0 <= st["p"] <= c


def test_arc_resident_equals_t1_union_t2():
    rng = random.Random(7)
    trace = [rng.randrange(30) for _ in range(1000)]
    p = ARC(6)
    p.run(trace)
    st = p.state()
    assert p.resident == (set(st["T1"]) | set(st["T2"]))
