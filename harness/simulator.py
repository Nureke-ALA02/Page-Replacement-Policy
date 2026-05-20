"""
CLI entrypoint:

    python -m harness.simulator --policy lru --capacity 64 --trace traces/zipf.txt
    python -m harness.simulator --all --capacity 64 --trace traces/zipf.txt
    python -m harness.simulator --policy fifo --capacity 3 --inline 1,2,3,4,1,2,5,1,2,3,4,5

The CLI is intentionally thin — it exists so reviewers (and the
instructor at the defense) can poke at the system without writing Python.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Allow running as `python -m harness.simulator` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from policies import REGISTRY  # noqa: E402
from harness.trace_loader import load_trace  # noqa: E402
from harness.metrics import simulate, classify_misses  # noqa: E402


def parse_inline(s: str) -> list[int]:
    return [int(x) for x in s.replace(",", " ").split() if x]


def run_one(name: str, capacity: int, trace: list[int], extra_args=None):
    cls = REGISTRY[name]
    kwargs = extra_args or {}
    policy = cls(capacity, **kwargs)
    res = simulate(policy, trace)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Page replacement simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--trace", help="path to a trace file (.txt or .txt.gz)")
    src.add_argument("--inline", help="comma- or space-separated pages")

    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument("--policy", choices=sorted(REGISTRY), help="single policy")
    sel.add_argument("--all", action="store_true", help="run every policy")

    ap.add_argument("--capacity", type=int, required=True,
                    help="number of physical frames")
    ap.add_argument("--classify", action="store_true",
                    help="also compute 3C miss classification (uses OPT)")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args(argv)

    if args.trace:
        trace = load_trace(args.trace)
        src_label = args.trace
    else:
        trace = parse_inline(args.inline)
        src_label = f"inline({len(trace)} refs)"

    if args.verbose:
        print(f"# trace: {src_label}, length={len(trace)}, "
              f"unique={len(set(trace))}, capacity={args.capacity}")

    names = sorted(REGISTRY) if args.all else [args.policy]

    # Pretty table header
    print(f"{'policy':<10} {'cap':>5} {'refs':>10} {'hits':>10} "
          f"{'faults':>10} {'fault_rate':>11}")
    print("-" * 60)
    for name in names:
        res = run_one(name, args.capacity, trace)
        print(f"{res.policy:<10} {res.capacity:>5d} {res.refs:>10d} "
              f"{res.hits:>10d} {res.faults:>10d} {res.fault_rate:>11.4f}")

    if args.classify:
        # Classify for whichever last-run policy (or each).
        for name in names:
            cls = REGISTRY[name]
            policy = cls(args.capacity)
            res = simulate(policy, trace)
            c = classify_misses(trace, args.capacity, res.faults)
            print(f"\n3C breakdown for {res.policy} @ cap={args.capacity}:")
            for k, v in c.items():
                print(f"  {k:<14} {v}")


if __name__ == "__main__":
    main()
