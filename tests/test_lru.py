import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
from policies import LRU


def test_basic():
    p = LRU(3)
    p.run([1, 2, 3])
    assert p.faults == 3
    p.access(1)
    p.access(4)
    assert 2 not in p.resident
    assert {1, 3, 4} == p.resident


def test_lru_evicts_least_recently_used():
    p = LRU(3)
    p.run([1, 2, 3, 1, 4])
    assert 2 not in p.resident


def test_no_belady_anomaly_random():
    rng = random.Random(0)
    for seed in range(5):
        rng2 = random.Random(seed)
        trace = [rng2.randrange(20) for _ in range(2000)]
        prev = None
        for cap in range(1, 21):
            p = LRU(cap)
            p.run(trace)
            if prev is not None:
                assert p.faults <= prev, (
                    f"LRU got worse with more memory: cap={cap-1} -> {cap}, "
                    f"{prev} -> {p.faults} (seed={seed})"
                )
            prev = p.faults


def test_lru_pessimal_on_looping():
    N = 10
    seq = [i % N for i in range(100)]
    p = LRU(N - 1)
    p.run(seq)
    expected_faults = 100 - 0
    assert p.faults == 100
