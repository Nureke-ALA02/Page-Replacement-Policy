"""
Generate a 'realistic' trace by simulating the memory-access pattern of
a matrix multiply. This isn't quite the same as a true valgrind trace,
but it captures three real phenomena:

  1. Row-major scans (cache friendly).
  2. Column-major scans (cache hostile — strided).
  3. Mixed working sets (the dot-product accumulator stays hot).

We use this as a backup "real-ish" workload when valgrind isn't
available. It's strong enough to show meaningful differences between
LRU, ARC, Aging, and FIFO.

Run as:  python -m traces.matmul_trace
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.trace_loader import save_trace


def matmul_trace(n: int = 64, page_bytes: int = 4096,
                 element_bytes: int = 8) -> list[int]:
    """Simulate page accesses for C = A * B with three n*n matrices.

    Pages are virtual: A starts at page 0, B at page off_b, C at off_c.
    For an n*n*8B matrix (doubles), each row is n*8 bytes, so pages per
    row = ceil(n*8 / 4096). For n=64: 64*8 = 512 bytes — half a page,
    so each pair of rows shares a page.
    """
    rows_per_page = max(1, page_bytes // (n * element_bytes))
    pages_per_matrix = (n + rows_per_page - 1) // rows_per_page

    off_a = 0
    off_b = pages_per_matrix
    off_c = 2 * pages_per_matrix

    def page_of(mat_off: int, row: int, col: int) -> int:
        # Treat each matrix as row-major; col index only matters for
        # very wide matrices. For our n*8B row layout we can ignore it.
        _ = col  # noqa: F841 (kept for clarity)
        return mat_off + row // rows_per_page

    refs: list[int] = []
    # Standard ijk matrix multiply: C[i][j] += A[i][k] * B[k][j].
    # The access pattern: A[i][*] is row-major (cache-friendly),
    # B[*][j] is column-major (strided — cache-hostile).
    for i in range(n):
        for j in range(n):
            refs.append(page_of(off_c, i, j))  # C[i][j] write
            for k in range(n):
                refs.append(page_of(off_a, i, k))  # A[i][k]
                refs.append(page_of(off_b, k, j))  # B[k][j] — strided!
                refs.append(page_of(off_c, i, j))  # accumulate
    return refs


def main() -> None:
    out = Path(__file__).resolve().parent / "data" / "matmul_64.txt"
    refs = matmul_trace(n=64)
    save_trace(out, refs,
               header="simulated 64x64 matmul page-access trace "
                      f"({len(refs)} refs, "
                      f"{len(set(refs))} unique pages)")
    print(f"wrote {out}  ({len(refs)} refs, {len(set(refs))} pages)")


if __name__ == "__main__":
    main()
