"""Simulator engine, trace I/O, and metrics."""

from .trace_loader import load_trace, iter_trace, save_trace
from .metrics import simulate, classify_misses, Result

__all__ = ["load_trace", "iter_trace", "save_trace",
           "simulate", "classify_misses", "Result"]
