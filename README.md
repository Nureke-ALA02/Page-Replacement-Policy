# Page Replacement Policy Lab

A simulator and analysis harness for classic page-replacement algorithms.
Implements **FIFO, LRU, Belady's Optimal (OPT), Clock (Second-Chance),
LFU, Aging, and ARC**, runs them on synthetic and real workloads, and
produces the plots that explain *why* one policy beats another on a
given trace — including a clean demonstration of **Belady's anomaly**.

Built for the final project of the **Computer Architecture & Operating
Systems** course (topic #12). The full development was driven by AI
agents — see `AI_USAGE.md` for prompts, sessions, and how we kept the
generated code under control.

---

## Quick start

```bash
# 1. Set up the environment (Python 3.10+ recommended).
pip install -r requirements.txt

# 2. Generate the synthetic traces (~1 second).
python -m traces.generate_all

# 3. Run a single experiment.
python -m harness.simulator --all --capacity 30 \
    --trace traces/data/zipf_a1_1k_100p.txt --classify

# 4. Or rebuild every plot end-to-end (~2 minutes).
python -m experiments.run_all

# 5. Run the test suite (~0.2 s, 41 tests).
pytest tests/ -v
```

Plots land in `experiments/plots/`. Everything is reproducible from
seed: re-running the suite produces the same numbers.

---

## What the project shows

The five things we demonstrate at the defense:

1. **Belady's anomaly.** On the canonical 12-reference sequence
   `1,2,3,4,1,2,5,1,2,3,4,5`, FIFO produces 9 faults with 3 frames
   but 10 faults with 4 frames — *more memory, more faults*. LRU and
   OPT (both stack algorithms) produce monotonically non-increasing
   curves on the same trace.
   *See `plots/belady_anomaly.png`.*

2. **OPT is the lower bound.** For every workload at every capacity,
   no online policy beats OPT. We lock this in with a property test
   (`tests/test_opt.py::test_opt_beats_or_ties_online`).

3. **The right policy depends on the workload.**
   - On Zipfian access patterns (`zipf_a1_*`), LFU and ARC win.
   - On looping access (working set just larger than cache), LRU is
     catastrophic — every reference faults — but Aging is much better.
   - On uniform random, everything converges; locality is the lever.

4. **Thrashing.** Plotting fault rate vs cache size on a working-set
   workload shows the characteristic knee at capacity = working-set
   size. Below it, the program faults on almost every reference;
   above it, the cache mostly hits.
   *See `plots/thrashing.png`.*

5. **3C miss classification (Hill 1987).** Each policy's faults split
   into *compulsory* (cold), *capacity* (would happen even under OPT),
   and *conflict* (extra misses caused by the replacement choice).
   The compulsory and capacity bars are identical across policies —
   only the conflict component differs. That difference is exactly
   what page-replacement policies are competing on.
   *See `plots/miss_classification.png`.*

---

## Project layout

```
page-replacement-lab/
├── README.md
├── AI_USAGE.md             # which AI tools we used and how
├── requirements.txt
├── Makefile                # convenience: make test / make plots
│
├── policies/               # the seven replacement policies
│   ├── base.py             # abstract Policy + OracleNeedsTrace mixin
│   ├── fifo.py             # FIFO        — can show Belady's anomaly
│   ├── lru.py              # LRU         — stack algorithm
│   ├── optimal.py          # Belady OPT  — offline lower bound
│   ├── clock.py            # Second-Chance — LRU approximation
│   ├── lfu.py              # LFU         — count-based
│   ├── aging.py            # Aging       — 8-bit LFU + decay
│   └── arc.py              # ARC         — adaptive (T1/T2/B1/B2)
│
├── harness/                # simulator engine
│   ├── simulator.py        # CLI: --policy / --all / --capacity / --trace
│   ├── trace_loader.py     # text + gzip + inline traces
│   └── metrics.py          # Result, simulate(), classify_misses()
│
├── traces/
│   ├── synthetic.py        # uniform / zipf / looping / working-set / ...
│   ├── generate_all.py     # produces traces/data/*.txt
│   └── data/               # generated traces (gitignored)
│
├── experiments/
│   ├── belady_anomaly.py   # the famous 12-ref demo
│   ├── belady_curves.py    # faults vs capacity for every trace
│   ├── thrashing.py        # fault rate vs cache size
│   ├── miss_classification.py  # 3C stacked bar chart
│   ├── run_all.py          # runs every experiment
│   └── plots/              # generated PNGs
│
└── tests/                  # pytest — 41 tests
    ├── test_fifo.py        # incl. Belady anomaly lock-in
    ├── test_lru.py         # incl. stack-property check on random traces
    ├── test_opt.py         # incl. OPT-is-lower-bound property test
    ├── test_other_policies.py
    └── test_invariants.py  # invariants every policy must satisfy
```

---

## The policies, in one paragraph each

**FIFO.** The oldest-loaded page is evicted regardless of use pattern.
Simple and cheap. Not a stack algorithm, so it can exhibit Belady's
anomaly — making it pedagogically valuable but not usable in practice.

**LRU.** Evict the page used longest ago. Cannot show Belady's anomaly
(stack property). Strong on most workloads but catastrophically bad on
loops larger than the cache. Implementation here uses `OrderedDict` for
O(1) hit and O(1) eviction.

**OPT (Belady).** On a fault, evict the page whose *next* reference is
furthest in the future. Optimal, but offline — needs the whole trace
up front. Used here as a lower bound to attribute "conflict" misses
to each online policy.

**Clock (Second-Chance).** A circular buffer with one reference bit
per frame. Hand sweeps; if ref=0 evict, else clear ref and advance.
LRU-like quality at near-zero per-access cost. Linux, FreeBSD, and
most production OSes use Clock variants.

**LFU.** Evict lowest reference count. Strong on heavily skewed
(Zipfian) workloads — popular pages stay resident. Weakness: pages
that were hot once and never again stay forever.

**Aging.** Per-page 8-bit shift register; on each clock tick the
register is shifted right with the ref bit ORed into the high bit.
This gives recency-weighted frequency at the cost of one byte per
page. Combines the strengths of LFU and LRU.

**ARC (Megiddo & Modha, FAST '03).** Splits the cache between a
recency list (T1) and a frequency list (T2), with two "ghost" lists
(B1, B2) holding the IDs of pages recently evicted from each. The
partition parameter `p` is adapted online based on which ghost list
is producing more hits. Used in ZFS and many production caches.

---

## CLI reference

```bash
# Run one policy on one trace
python -m harness.simulator --policy lru --capacity 64 \
    --trace traces/data/zipf_a1_1k_100p.txt

# Run every policy at once for direct comparison
python -m harness.simulator --all --capacity 64 \
    --trace traces/data/zipf_a1_1k_100p.txt

# Use an inline trace (great for the live demo)
python -m harness.simulator --policy fifo --capacity 3 \
    --inline 1,2,3,4,1,2,5,1,2,3,4,5

# Add 3C breakdown
python -m harness.simulator --all --capacity 30 \
    --trace traces/data/zipf_a1_1k_100p.txt --classify
```

---

## Reproducibility

Every random generator takes an explicit `seed`. The default seeds in
`traces/generate_all.py` reproduce the exact numbers in the slides.
There are no clocks, threads, or external services involved.

Python 3.10+ is required (we use modern type-hint syntax). The only
non-stdlib dependency is `matplotlib` for plotting and `pytest` for
the test suite.

---

## Team

This project was built by team **{TEAM NAME}** as the final exam
deliverable for the *Computer Architecture & Operating Systems* course.

| Member | Role |
|--------|------|
| {Nurdaulet} | Harness, simulator core, trace loader |
| {Sultan} | FIFO, LRU, OPT, and their tests |
| {Zhanel} | Clock, LFU, Aging, and their tests |
| {Alua} | ARC (the hardest one) |
| {Altynbek} | Synthetic trace generators + real-trace ingest |
| {Zhadyra} | Experiments, plots, and presentation |

See `git log` and the `AI_USAGE.md` notes for individual contributions.

---

## License

Course project, not licensed for redistribution.
