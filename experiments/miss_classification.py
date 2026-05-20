"""
3C miss classification visualization.

For a chosen trace at a fixed capacity, compute the Hill (1987)
breakdown of misses into:
    compulsory  — first-ever reference to the page
    capacity    — present even under OPT (i.e., insufficient memory)
    conflict    — extra misses caused by replacement policy choices
                  (above what OPT would have made)

We plot a stacked bar per policy. The compulsory and capacity components
are identical across policies (they depend only on the trace and the
capacity), so the visible difference between bars is the **conflict**
component — that is the part each policy is responsible for.
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
from harness.metrics import simulate, classify_misses


def main() -> None:
    trace_path = Path(__file__).resolve().parent.parent / "traces" / "data" \
        / "zipf_a1_1k_100p.txt"
    trace = load_trace(trace_path)
    cap = 30

    # Compute the OPT bound (capacity miss baseline) once.
    rows = []
    for name in sorted(REGISTRY):
        cls = REGISTRY[name]
        p = cls(cap)
        r = simulate(p, trace)
        c = classify_misses(trace, cap, r.faults)
        rows.append((cls.__name__, c["compulsory"],
                     c["capacity"], c["conflict"]))

    names = [r[0] for r in rows]
    compulsory = [r[1] for r in rows]
    capacity = [r[2] for r in rows]
    conflict = [r[3] for r in rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(names, compulsory, label="compulsory (cold)",
           color="tab:gray")
    ax.bar(names, capacity, bottom=compulsory,
           label="capacity", color="tab:blue")
    ax.bar(names, conflict,
           bottom=[a + b for a, b in zip(compulsory, capacity)],
           label="conflict (policy)", color="tab:red")

    ax.set_ylabel("Page faults")
    ax.set_title(f"3C miss classification @ capacity={cap}\n"
                 f"Trace: {trace_path.name} ({len(trace)} refs)")
    ax.legend(loc="upper left")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    out = Path(__file__).resolve().parent / "plots" / "miss_classification.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
