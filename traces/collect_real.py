"""
Real-trace collection from running programs.

We use Valgrind's `lackey` tool, which logs every memory access of a
target binary. We then convert virtual addresses to page numbers
(default page size 4 KiB = 12-bit offset) and write the result in our
trace format.

Why this matters for the project:
  Synthetic traces are useful for showing specific phenomena (looping
  for LRU pessimal case, Belady sequence for FIFO anomaly), but they
  don't tell you how policies behave on actual code. A real trace from
  running `ls -lR`, `gcc`, or our own programs gives reviewers something
  concrete to point at.

Usage:
    # 1. Make sure valgrind is installed:
    #      apt install valgrind                (Debian/Ubuntu)
    #      brew install valgrind               (macOS — limited support)
    # 2. Collect a trace:
    python -m traces.collect_real --cmd "ls -lR /usr/include" \\
        --out traces/real/ls_lR.txt --max-refs 200000
    # 3. Use it like any other trace:
    python -m harness.simulator --all --capacity 64 \\
        --trace traces/real/ls_lR.txt

If valgrind is not available, this script is a no-op and the project
falls back to synthetic traces (which are already enough for every
required demo).
"""

from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.trace_loader import save_trace


PAGE_BITS_DEFAULT = 12  # 4 KiB pages


def have_valgrind() -> bool:
    return shutil.which("valgrind") is not None


def collect(cmd: str, out_path: Path, max_refs: int,
            page_bits: int = PAGE_BITS_DEFAULT) -> None:
    """Run `cmd` under valgrind+lackey, parse the trace, write to out_path.

    lackey's `--trace-mem=yes` output looks like:
        I  0804828f,3      <- instruction fetch (addr, size)
         L 1ffeff688c,4    <- load
         S 1ffeff688c,4    <- store
         M 1ffeff688c,4    <- modify (load + store)
    We treat every line as a memory reference; the address is hex,
    we shift right by `page_bits` to get the page number.

    Output is normalized: page IDs are mapped to dense 0..N-1 integers
    so the trace file stays compact and the simulator's `set()` lookups
    stay fast.
    """
    if not have_valgrind():
        raise RuntimeError(
            "valgrind not found in PATH. Install it or use a synthetic "
            "trace instead. The project's required demos work without "
            "valgrind."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # We pipe valgrind's stderr through a Python loop so we can stop
    # after `max_refs` without waiting for the full program to finish.
    full_cmd = ["valgrind", "--tool=lackey", "--trace-mem=yes",
                "--log-fd=2", "--"] + cmd.split()
    print(f"running: {' '.join(full_cmd)}")
    print(f"capping at {max_refs} references; ctrl-C if it takes too long")

    pages: list[int] = []
    page_id_map: dict[int, int] = {}
    next_id = 0

    proc = subprocess.Popen(
        full_cmd, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True, bufsize=1,
    )
    try:
        assert proc.stderr is not None
        for line in proc.stderr:
            line = line.strip()
            # Lines we care about start with 'I ', ' L', ' S', or ' M'
            if not line or line[0] not in (" ", "I"):
                continue
            # Split off the kind prefix; we don't care which.
            parts = line.split()
            if len(parts) < 2:
                continue
            addr_size = parts[-1] if "," in parts[-1] else parts[1]
            if "," not in addr_size:
                continue
            addr_hex = addr_size.split(",", 1)[0]
            try:
                page_raw = int(addr_hex, 16) >> page_bits
            except ValueError:
                continue
            pid = page_id_map.get(page_raw)
            if pid is None:
                pid = next_id
                page_id_map[page_raw] = pid
                next_id += 1
            pages.append(pid)
            if len(pages) >= max_refs:
                break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

    header = (f"real trace collected via valgrind lackey\n"
              f"cmd: {cmd}\n"
              f"page_bits: {page_bits} (page size {1 << page_bits} bytes)\n"
              f"references: {len(pages)}\n"
              f"unique pages: {len(page_id_map)}")
    save_trace(out_path, pages, header=header)
    print(f"wrote {out_path} ({len(pages)} refs, {len(page_id_map)} pages)")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Collect a real memory-access trace via valgrind lackey")
    ap.add_argument("--cmd", required=True,
                    help='shell command to trace, e.g. "ls -lR /usr/include"')
    ap.add_argument("--out", type=Path, required=True,
                    help="output trace path")
    ap.add_argument("--max-refs", type=int, default=200_000,
                    help="stop after this many memory references")
    ap.add_argument("--page-bits", type=int, default=PAGE_BITS_DEFAULT,
                    help="log2 of page size (default 12 = 4 KiB)")
    args = ap.parse_args()

    if not have_valgrind():
        print("ERROR: valgrind is not installed.", file=sys.stderr)
        print("       On Ubuntu/Debian: sudo apt install valgrind",
              file=sys.stderr)
        print("       The project's required demos still work without it.",
              file=sys.stderr)
        sys.exit(1)

    collect(args.cmd, args.out, args.max_refs, args.page_bits)


if __name__ == "__main__":
    main()
