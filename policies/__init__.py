"""Page replacement policies.

The `REGISTRY` mapping is what the simulator and experiment scripts use
to look up a policy by name. Add new policies here and they immediately
become available on the CLI.
"""

from .base import Policy, OracleNeedsTrace
from .fifo import FIFO
from .lru import LRU
from .optimal import OPT
from .clock import Clock
from .lfu import LFU
from .aging import Aging
from .arc import ARC

REGISTRY = {
    "fifo": FIFO,
    "lru": LRU,
    "opt": OPT,
    "clock": Clock,
    "lfu": LFU,
    "aging": Aging,
    "arc": ARC,
}

__all__ = [
    "Policy", "OracleNeedsTrace", "FIFO", "LRU", "OPT",
    "Clock", "LFU", "Aging", "ARC", "REGISTRY",
]
