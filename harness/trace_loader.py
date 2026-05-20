"""
Trace loading.

A trace is a sequence of page numbers, one access per element. We support
two input formats:

  - Plain text, one integer per line. Blank lines and lines starting with
    `#` are ignored.
  - Gzipped version of the above (.txt.gz).

We also support an in-memory "trace name" shortcut for built-in synthetic
traces — handy from the CLI: e.g. `--trace synthetic:zipf:n=1000,pages=100`.
"""

from __future__ import annotations
import gzip
from pathlib import Path
from typing import List, Iterator


def load_trace(path: str | Path) -> List[int]:
    """Load a trace from disk into a list of ints. Use this when you need
    random access (e.g. for OPT). For huge traces, prefer `iter_trace`."""
    return list(iter_trace(path))


def iter_trace(path: str | Path) -> Iterator[int]:
    """Stream a trace one page at a time. Memory-friendly for big traces."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                yield int(line)
            except ValueError:
                raise ValueError(
                    f"{path}:{lineno}: expected integer page id, got {line!r}"
                )


def save_trace(path: str | Path, pages, header: str | None = None) -> None:
    """Write a trace (iterable of ints) to disk. Gzipped if path ends .gz."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt") as f:
        if header:
            for line in header.splitlines():
                f.write(f"# {line}\n")
        for p in pages:
            f.write(f"{p}\n")
