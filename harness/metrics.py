"""
Metrics computed from a simulator run.

Beyond raw fault count, we expose two classical breakdowns:

  - Hit / fault rates.
  - 3C miss classification (Hill, 1987):
      * compulsory ("cold") — first time we ever see the page; unavoidable
      * capacity — would not have happened with infinite memory
      * conflict — replacement-policy artifact: it would not have happened
        with the optimal policy (OPT) at the same capacity

  The 3C breakdown requires running OPT alongside the policy under test.
  We compute it post-hoc.
"""

from dataclasses import dataclass
from typing import List
from policies import Policy, OPT
from policies.base import OracleNeedsTrace


@dataclass
class Result:
    policy: str
    capacity: int
    refs: int
    hits: int
    faults: int

    @property
    def hit_rate(self) -> float:
        return self.hits / self.refs if self.refs else 0.0

    @property
    def fault_rate(self) -> float:
        return self.faults / self.refs if self.refs else 0.0


def simulate(policy: Policy, trace: List[int]) -> Result:
    """Run `policy` over `trace`. Returns a Result. Mutates `policy`."""
    if isinstance(policy, OracleNeedsTrace):
        policy.set_trace(trace)
    for p in trace:
        policy.access(p)
    return Result(
        policy=policy.name,
        capacity=policy.capacity,
        refs=policy.total_refs,
        hits=policy.hits,
        faults=policy.faults,
    )


def classify_misses(trace: List[int], capacity: int, policy_faults: int) -> dict:
    """3C classification.

    Returns a dict with keys: compulsory, capacity, conflict, total.
    `policy_faults` is the fault count from whichever online policy you
    want to attribute conflict misses to.
    """
    compulsory = len(set(trace))
    opt = OPT(capacity)
    opt.set_trace(trace)
    for p in trace:
        opt.access(p)
    opt_faults = opt.faults
    # Faults OPT could not avoid at this capacity, minus the unavoidable
    # cold misses, are capacity misses.
    cap = max(0, opt_faults - compulsory)
    # Everything else our policy missed beyond OPT is conflict.
    conflict = max(0, policy_faults - opt_faults)
    return {
        "compulsory": compulsory,
        "capacity": cap,
        "conflict": conflict,
        "total": compulsory + cap + conflict,
        "policy_faults": policy_faults,
        "opt_faults": opt_faults,
    }
