"""
Run every experiment in sequence and produce all plots.

This is the script we run during the live demo at the defense:
it generates traces, computes all metrics, and writes plots in
~30 seconds on a modest laptop.
"""

from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Each `main` is the entrypoint of an experiment script.
from experiments import belady_curves, belady_anomaly, thrashing, miss_classification


def run(name: str, fn) -> None:
    t0 = time.time()
    print(f"\n=== {name} ===")
    fn()
    print(f"({time.time() - t0:.1f}s)")


def main() -> None:
    # Make sure traces exist.
    data = Path(__file__).resolve().parent.parent / "traces" / "data"
    if not any(data.glob("*.txt")):
        print("No traces in traces/data — generating now.")
        from traces import generate_all
        generate_all.main()

    run("Belady anomaly demo", belady_anomaly.main)
    run("Belady curves (all traces)", belady_curves.main)
    run("Thrashing analysis", thrashing.main)
    run("3C miss classification", miss_classification.main)


if __name__ == "__main__":
    main()
