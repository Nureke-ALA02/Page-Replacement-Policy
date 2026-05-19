import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
from policies import OPT, FIFO, LRU, Clock, LFU, Aging, ARC
from harness.metrics import simulate

def run_opt(trace, cap):
    p = OPT(cap)
    p.set_trace(trace)
    p.run(trace)
    return p.faults

def test_belady_example_3frames():
    seq = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    assert run_opt(seq, 3) == 7

def test_opt_beats_or_ties_online():
    rng = random.Random(7)
    trace = [rng.randrange(15) for _ in range(500)]
    cap = 4
    opt_faults = run_opt(trace, cap)
    for cls in [FIFO, LRU, Clock, LFU, Aging, ARC]:
        p = cls(cap)
        simulate(p, trace)
        assert opt_faults <= p.faults, (
            f"OPT({opt_faults}) > {p.name}({p.faults}) — OPT is not "
            f"optimal, something is wrong."
        )

def test_never_used_again_is_perfect_victim():
    trace = [1, 2, 3, 4, 1, 3]
    p = OPT(3)
    p.set_trace(trace)
    p.run(trace)
    assert 2 not in p.resident