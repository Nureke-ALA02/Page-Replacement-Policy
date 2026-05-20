"""
Belady curves: page faults as a function of cache capacity.

For each trace and each policy, we sweep capacity over a range and plot
the resulting fault count. This is the canonical view of policy quality:
  - OPT is always at the bottom (lower bound).
  - LRU usually tracks close to OPT on locality-rich traces.
  - LFU/ARC may beat LRU on skewed workloads.
  - All curves should be monotonically non-increasing for stack
    algorithms (LRU, OPT). FIFO is *not* monotonic in general — see
    the separate `belady_anomaly.py` script for that demonstration.

Output: experiments/plots/belady_<trace_name>.png
"""

from __future__ import annotations
import sys
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from policies import REGISTRY
from harness.trace_loader import load_trace
from harness.metrics import simulate


# Visual style — distinct colors and markers so the plot is legible
# even printed in black and white.
STYLE = {
    "OPT":   {"color": "black",   "marker": "*", "linestyle": "-",  "linewidth": 2.0},
    "LRU":   {"color": "tab:blue", "marker": "o", "linestyle": "-"},
    "ARC":   {"color": "tab:red",  "marker": "s", "linestyle": "-"},
    "Clock": {"color": "tab:green", "marker": "^", "linestyle": "--"},
    "FIFO":  {"color": "tab:orange", "marker": "v", "linestyle": "--"},
    "LFU":   {"color": "tab:purple", "marker": "D", "linestyle": ":"},
    "Aging": {"color": "tab:brown", "marker": "x", "linestyle": ":"},
}


def belady_curve(trace_path: Path, capacities: list[int], out_dir: Path) -> None:
    trace = load_trace(trace_path)
    name = trace_path.stem
    unique = len(set(trace))
    print(f"  trace={name}  refs={len(trace)}  unique={unique}")

    fig, ax = plt.subplots(figsize=(8, 5))
    for pname, cls in REGISTRY.items():
        faults = []
        for cap in capacities:
            p = cls(cap)
            r = simulate(p, trace)
            faults.append(r.faults)
        style = STYLE.get(cls.__name__, {})
        ax.plot(capacities, faults, label=cls.__name__, **style)

    ax.set_xlabel("Cache capacity (frames)")
    ax.set_ylabel("Page faults")
    ax.set_title(f"Belady curve: {name}\n"
                 f"({len(trace)} refs, {unique} unique pages)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", frameon=True)
    fig.tight_layout()

    out = out_dir / f"belady_{name}.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"  wrote {out}")


def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "traces" / "data"
    out_dir = Path(__file__).resolve().parent / "plots"
    out_dir.mkdir(exist_ok=True)

    # Sweep cache size from very small to where most policies converge.
    capacities_small = list(range(2, 21, 2))      # for tiny synthetic
    capacities_med = list(range(5, 101, 5))       # for 100-page workloads
    capacities_large = list(range(10, 201, 10))   # for 500-page seqscan

    # Pair each trace with a sensible capacity sweep.
    plans = {
        "belady_demo.txt":          capacities_small,
        "uniform_1k_100p.txt":      capacities_med,
        "zipf_a1_1k_100p.txt":      capacities_med,
        "zipf_a2_1k_100p.txt":      capacities_med,
        "looping_50p.txt":          list(range(2, 71, 4)),
        "workingset_50p.txt":       capacities_med,
        "seqscan_500p.txt":         capacities_large,
    }

    for tname, caps in plans.items():
        tpath = data_dir / tname
        if not tpath.exists():
            print(f"skip {tname} (not generated yet)")
            continue
        belady_curve(tpath, caps, out_dir)


if __name__ == "__main__":
    main()
