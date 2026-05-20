"""
Generate the standard set of synthetic traces used by the experiments.

Run as:  python -m traces.generate_all

Outputs go into traces/data/*.txt. We keep them small enough to commit
(~1MB total, gzipped). If you need bigger traces, edit N_REFS below.
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.trace_loader import save_trace
from traces import synthetic

N_REFS = 30_000  # keeps the full experiment suite under a minute
OUT = Path(__file__).resolve().parent / "data"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    specs = [
        ("uniform_1k_100p.txt",
         synthetic.uniform_random(N_REFS, 100, seed=42),
         "uniform random over 100 pages"),
        ("zipf_a1_1k_100p.txt",
         synthetic.zipf(N_REFS, 100, alpha=1.0, seed=42),
         "Zipf alpha=1.0 over 100 pages"),
        ("zipf_a2_1k_100p.txt",
         synthetic.zipf(N_REFS, 100, alpha=2.0, seed=42),
         "Zipf alpha=2.0 over 100 pages (heavily skewed)"),
        ("looping_50p.txt",
         synthetic.looping(N_REFS, 50),
         "looping 1..50,1..50,... — LRU pessimal at cap=49"),
        ("workingset_50p.txt",
         synthetic.working_set(N_REFS, 200, ws_size=50,
                               shift_every=2000, shift_by=10, seed=42),
         "drifting working set of 50 pages within 200"),
        ("seqscan_500p.txt",
         synthetic.sequential_scan(N_REFS, 500),
         "sequential scan through 500 pages"),
        ("belady_demo.txt",
         synthetic.belady_anomaly(),
         "classic 12-ref Belady's anomaly demo"),
    ]
    for name, trace, desc in specs:
        path = OUT / name
        save_trace(path, trace, header=desc)
        print(f"wrote {path}  ({len(trace)} refs)")


if __name__ == "__main__":
    main()
