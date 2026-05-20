"""
Thrashing analysis.

When a program's *working set* (the set of pages it actively uses) is
larger than physical memory, every replacement decision evicts a page
that will soon be referenced again. The fault rate sharply rises — the
system spends more time paging than computing. This is **thrashing**.

We demonstrate it with a working-set trace whose hot set has fixed size
W. Sweeping cache capacity from below W to above W, we plot fault rate.
The "knee" of the curve, around capacity = W, is the visible signature of
thrashing — to the left of the knee, the program thrashes; to the right,
it runs efficiently.

We also overlay an "always-resident" reference: if the cache were large
enough for the *entire* page set, only cold misses remain.
"""

from __future__ import annotations
import sys
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from policies import LRU, ARC, Clock, OPT
from harness.metrics import simulate
from traces.synthetic import working_set


def main() -> None:
    N_REFS = 50_000
    N_PAGES = 200
    WS = 60                  # the hot working set size
    trace = working_set(N_REFS, N_PAGES, ws_size=WS,
                        shift_every=2_000, shift_by=5, seed=0)

    caps = list(range(5, 121, 5))
    series = {"OPT": [], "LRU": [], "ARC": [], "Clock": []}

    for cap in caps:
        for name, cls in [("OPT", OPT), ("LRU", LRU),
                          ("ARC", ARC), ("Clock", Clock)]:
            p = cls(cap)
            r = simulate(p, trace)
            series[name].append(r.fault_rate)

    fig, ax = plt.subplots(figsize=(8, 5))
    styles = {
        "OPT":   ("black", "*-"),
        "LRU":   ("tab:blue", "o-"),
        "ARC":   ("tab:red", "s-"),
        "Clock": ("tab:green", "^--"),
    }
    for n, ys in series.items():
        color, marker = styles[n]
        ax.plot(caps, ys, marker, color=color, label=n, linewidth=2)

    ax.axvline(WS, color="gray", linestyle=":", alpha=0.7)
    ax.text(WS + 1, max(series["OPT"]) * 0.9,
            f"working set\nsize ≈ {WS}", color="gray", fontsize=10)

    ax.set_xlabel("Cache capacity (frames)")
    ax.set_ylabel("Page fault rate")
    ax.set_title("Thrashing: fault rate vs cache size\n"
                 f"Drifting working set ({WS} hot pages in {N_PAGES} total)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()

    out = Path(__file__).resolve().parent / "plots" / "thrashing.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
