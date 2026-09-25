# Research Continuation: DDFSIM Crosstalk Fault Simulation

This note documents the next course-project stage after the Smart Staggering work. The implementation itself is maintained separately; this repository contains the earlier software-mitigation prototype.

## Motivation

The first project asks how scheduling can reduce crosstalk. The continuation asks a different systems question: **how can large crosstalk fault campaigns be represented reproducibly and dispatched efficiently across decision-diagram simulation engines?**

## Contribution 1 — hardware-grounded crosstalk fault generator

- Crosstalk is represented as a **persistent hardware vulnerability** tied to backend topology rather than one transient circuit-wide event.
- Candidate victims are enumerated from qubits and coupling edges.
- Triggering is a Boolean test: temporal overlap plus coupling-map distance within threshold `D`.
- Directionality is explicit and covers all four arity combinations: 1→1, 1→2, 2→1, and 2→2.
- Fault magnitude is selected from a discrete set of RZ rotations, making fault-list coverage reproducible and exactly countable.

For FakeGuadalupeV2 (16 qubits, 16 coupling edges), the single-fault cap is `(N + M) × 5 = 160`; the evaluated workloads realized **45–105 faults**.

## Contribution 2 — structure-aware simulator dispatcher

The dispatcher routes faults among decision-diagram simulation engines according to fault structure.

Pipeline:

1. Sparse faults take a fast path to prefix–suffix (`ps`).
2. The Python layer requests an `N × N` structural distance matrix from the C++ backend.
3. An Iterative Deepest Path Extraction heuristic forms chains of structurally similar faults.
4. Chain roots use `cawst`; nearby faults use `update_cawst` to exploit localized updates.
5. Faults are batched by engine/cluster and results are restored to original order.

## Evaluation

The prototype was evaluated on **seven algorithms** — QAOA, QFT, QFT-Entangled, AE, QPE-Exact, QNN, and VQE — at **10–12 qubits** on FakeGuadalupeV2.

Observed regimes:

- At 10 qubits, `ps` is the most robust general choice.
- On the hardest 10-qubit VQE workload, `ps` was the only engine to finish within the timeout, at roughly **102 s** and about **54 MB** peak memory.
- At 12 qubits on highly entangled QAOA/QFT-Entangled workloads, segment-based engines overtake `ps`.
- The results motivate structure-aware dispatch: no single simulation engine dominates every circuit/fault regime.

## Limitations

This is a course-project prototype. The benchmark width is modest, the backend topology is fixed, the trigger threshold and dispatcher cutoffs are empirical, and only the single-fault case is implemented. The next steps are multi-fault campaigns, automatic threshold tuning, broader backends, and direct end-to-end comparison of adaptive dispatch against the best fixed-engine baselines.
