# AI Usage

This is a mandatory part of the project. The course requires us to build
with AI agents and document how we used them. This file describes which
tools we used, how, and what we learned.

---

## Tools we used

- **Claude (Anthropic), web interface** — used as the primary
  architecture and design partner. We asked it to draft the project
  structure, the abstract `Policy` interface, and the harder policies
  (especially ARC). All code was reviewed and edited before committing.
- **Claude Code (CLI)** — used inside the repo for incremental edits,
  running tests, and debugging. Most commits were prepared in pair with
  Claude Code, with each team member driving their own session.
- **GitHub Copilot** — used in VSCode for inline completion during
  routine work (writing tests, type annotations, docstrings).

Per the project rules, the AI tools used are visible in:
- this file (`AI_USAGE.md`),
- the README,
- and commit messages — each commit that started from an AI session
  has a `[ai: <tool>]` tag in the message body.

---

## How we worked with AI

The honest summary: **AI accelerates everything, but it does not free
you from understanding your code.** Two principles that worked for us:

1. **Specify, don't ask vaguely.** Asking "implement ARC for me"
   produced confused code. Asking "implement ARC following Figure 4 of
   Megiddo & Modha 2003, with T1, T2, B1, B2 as OrderedDicts, and the
   four cases in `access` corresponding to the paper's four cases"
   produced something almost correct that we then fixed.
2. **Tests before trust.** For every policy we wrote at least one
   test we knew the answer to *by hand* (e.g., FIFO on the Belady
   sequence with 3 frames = 9 faults). If the AI's code passed that
   test, we trusted it enough to ship. If it didn't, we knew exactly
   where to look.

---

## Example prompts (representative, not exhaustive)

### Prompt 1 — Designing the policy interface

> We are building a page replacement simulator. Design an abstract
> base class `Policy` such that subclasses only need to implement
> three hooks: what to do on a hit, what to do on a miss with room,
> and how to pick a victim on a full miss. The base class should
> handle counters (hits, faults, resident set) and dispatch.
> Include a separate mixin for offline policies like OPT that need
> to see the entire trace in advance.

Result: roughly the structure of `policies/base.py`. We kept the
template-method design but renamed `evict_victim` to `_evict` for
consistency with private-by-convention naming.

### Prompt 2 — ARC was the hardest part

> Implement ARC (Adaptive Replacement Cache) from Megiddo & Modha,
> FAST 2003, "ARC: A Self-Tuning, Low Overhead Replacement Cache".
> Use the algorithm from Figure 4 of the paper directly. The four
> lists should be `OrderedDict`s. Be careful about the invariants:
> |T1| + |T2| ≤ c, |T1| + |B1| ≤ c, |T2| + |B2| ≤ 2c, and 0 ≤ p ≤ c.

The first response had a subtle bug in the adaptation of `p`: it
swapped the formulas for the B1-hit and B2-hit cases. We caught this
because our invariant test (`test_arc_invariants_after_random_workload`)
started failing after about 800 references. Fixed with a follow-up:

> The previous ARC had p increasing on a B2 hit. That is backwards:
> a hit in B2 means frequency is winning, so we should decrease p
> (give T1 less of the cache, T2 more). Please reread Figure 4 case
> II vs III carefully and fix.

### Prompt 3 — Caught Claude reproducing OSTEP-shaped code

When we asked Claude to "write the Aging algorithm", the first
version essentially reproduced OSTEP's pseudocode line-for-line.
We rewrote it from scratch ourselves so the implementation is ours,
keeping only the algorithmic structure (which is universal). The
test suite (`test_aging_basic`, `test_aging_capacity_invariant`)
was written by hand to confirm correctness.

### Prompt 4 — Debugging Belady's anomaly

When we first ran the anomaly experiment, FIFO showed 9 → 9 (not
9 → 10) at capacities 3 → 4. We thought the trace was wrong, then
realized our FIFO was secretly an LRU: someone had refactored
`_on_hit` to call `move_to_end` on the queue. We caught this by
running the FIFO tests against the canonical example with hand-
computed expected values. The Belady test now serves as a permanent
regression guard.

---

## What we did *not* let the AI do

- **Final design decisions.** Whether to use Python or C, whether to
  add real traces, what plots to produce — these came from team
  discussion. AI was a sounding board.
- **The presentation.** We wrote the slides ourselves so we'd own
  what we say on stage.
- **The Q&A.** Each team member is responsible for explaining their
  own code without AI help. The instructor will ask, "why does FIFO
  show the anomaly but LRU doesn't?" and we need to answer in our
  own words: because LRU is a stack algorithm (Mattson 1970) — the
  resident set with k+1 frames is always a superset of the resident
  set with k frames, so any reference that hits with k frames also
  hits with k+1.

---

## Per-member AI sessions

> **Format:** name, what was generated/edited with AI, what was done
> by hand. Update this section as we go.

- **{Nurdaulet}** — Used Claude to design `harness/simulator.py` CLI;
  wrote `harness/metrics.py` and `harness/trace_loader.py` by hand
  with Copilot completing boilerplate.
- **{Sultan}** — FIFO and LRU initial drafts via Claude Code; the
  Belady-anomaly tests written by hand to verify against textbook
  numbers. OPT prefix-index logic adapted from a Claude suggestion
  after profiling showed naive scan was the bottleneck.
- **{Zhanel}** — Clock written from scratch (the hand pointer needed
  edge-case attention Claude kept getting wrong); LFU and Aging via
  Claude Code with manual review of tiebreak logic.
- **{Alua}** — ARC. Three rounds of "implement, run tests, fix" with
  Claude. The final code is rewritten with explicit comments mapping
  each `if`/`elif` branch to a case of Figure 4 in the paper so we can
  defend it on Q&A.
- **{Altynbek}** — Synthetic trace generators written by hand
  (one-screen each); used Claude to suggest realistic parameter
  ranges for the Zipfian and working-set workloads. Real traces
  collected with `valgrind --tool=lackey --trace-mem=yes` on
  `ls -lR /usr` and post-processed by a Python script Claude drafted.
- **{Zhadyra}** — `experiments/` scripts and plotting via Claude;
  the choice of which plots to show on slides was a team discussion.
