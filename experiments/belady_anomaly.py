"""
Demonstrate Belady's anomaly.

For the classic sequence 1,2,3,4,1,2,5,1,2,3,4,5, we sweep cache capacity
from 1 to 7 and plot fault counts for FIFO, LRU, and OPT.

The interesting fact is at capacities 3 → 4 for FIFO:
   3 frames: 9 faults
   4 frames: 10 faults    ← MORE memory caused MORE faults
This is Belady's anomaly. Belady (1969) constructed this 12-element trace
specifically to exhibit it.

LRU and OPT, by contrast, are stack algorithms and produce monotonically
non-increasing curves.

This script prints the table and saves a plot.
"""

from __future__ import annotations
import sys
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from policies import FIFO, LRU, OPT
from traces.synthetic import belady_anomaly


def run(cls, cap, trace):
    p = cls(cap)
    if hasattr(p, "set_trace"):
        p.set_trace(trace)
    p.run(trace)
    return p.faults


def main() -> None:
    trace = belady_anomaly()
    caps = list(range(1, 8))

    rows = []
    for cap in caps:
        rows.append({
            "capacity": cap,
            "FIFO":  run(FIFO, cap, trace),
            "LRU":   run(LRU, cap, trace),
            "OPT":   run(OPT, cap, trace),
        })

    # Print a nice table.
    print(f"Trace: {trace}")
    print(f"{'cap':>4} {'FIFO':>5} {'LRU':>5} {'OPT':>5}  note")
    print("-" * 40)
    prev_fifo = None
    for r in rows:
        note = ""
        if prev_fifo is not None and r["FIFO"] > prev_fifo:
            note = "*** anomaly: FIFO got WORSE with more memory ***"
        print(f"{r['capacity']:>4d} {r['FIFO']:>5d} {r['LRU']:>5d} "
              f"{r['OPT']:>5d}  {note}")
        prev_fifo = r["FIFO"]

    # Plot.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(caps, [r["FIFO"] for r in rows], "v-",
            color="tab:orange", label="FIFO", linewidth=2)
    ax.plot(caps, [r["LRU"]  for r in rows], "o-",
            color="tab:blue", label="LRU", linewidth=2)
    ax.plot(caps, [r["OPT"]  for r in rows], "*-",
            color="black", label="OPT", linewidth=2)

    # Annotate the anomaly.
    ax.annotate(
        "Belady's anomaly:\nFIFO 3→4 frames\n9→10 faults",
        xy=(4, 10), xytext=(5, 11),
        arrowprops=dict(arrowstyle="->", color="red"),
        fontsize=11, color="red",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red"),
    )

    ax.set_xlabel("Cache capacity (frames)")
    ax.set_ylabel("Page faults")
    ax.set_title("Belady's anomaly demonstrated\n"
                 "Trace: 1,2,3,4,1,2,5,1,2,3,4,5")
    ax.set_xticks(caps)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()

    out = Path(__file__).resolve().parent / "plots" / "belady_anomaly.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
