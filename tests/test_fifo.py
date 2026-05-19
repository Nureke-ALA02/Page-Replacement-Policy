import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from policies import FIFO


def test_basic():
    p = FIFO(3)
    for x in [1, 2, 3]:
        assert p.access(x) is False
    assert p.faults == 3 and p.hits == 0
    assert p.access(1) is True
    assert p.access(4) is False
    assert p.access(1) is False


def test_belady_anomaly_3_frames():
    seq = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    p = FIFO(3)
    p.run(seq)
    assert p.faults == 9, f"expected 9 faults with 3 frames, got {p.faults}"


def test_belady_anomaly_4_frames():
    seq = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    p = FIFO(4)
    p.run(seq)
    assert p.faults == 10, f"expected 10 faults with 4 frames, got {p.faults}"


def test_resident_set_size():
    p = FIFO(3)
    p.run([1, 2, 3, 4, 5])
    assert len(p.resident) == 3
