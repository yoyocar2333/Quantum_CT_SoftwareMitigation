
# Research trajectory: from crosstalk mitigation to scalable fault simulation

This repository contains the **first stage** of a two-stage undergraduate quantum-computing research project.

## Stage 1 — Spatio-temporal crosstalk modeling and Smart Staggering

The first stage asks a compiler-level question: how can a scheduler reduce simultaneous-gate crosstalk without paying the full latency cost of serialization?

The implemented model combines:

- coupling-map distance decay;
- exact temporal overlap;
- asymmetric gate-pair coefficients;
- a coherent RZ phase-error component;
- probabilistic merging of multiple aggressors.

The mitigation layer compares Dense, Sparse, Smart Offline, and Smart Online schedules.

At the paper's reported `λ = 1` setting:

| Benchmark | Dense state fidelity | Smart Offline | Smart Online | Sparse | Smart Offline latency |
|---|---:|---:|---:|---:|---:|
| QFT | 0.1668 | **0.6910** | 0.4834 | 1.0000 | 1.17× |
| RCS | 0.4885 | **0.8028** | 0.7374 | 1.0000 | 1.62× |

The key systems insight is the trade-off: selective delay insertion recovers a large fraction of the lost state fidelity while preserving substantially more parallelism than full serialization.

## Stage 2 — DDFSIM crosstalk fault generation and simulator dispatch

The continuation project changes abstraction level. Instead of injecting a continuous noise process during one simulated execution, it treats crosstalk as a **hardware-tied fault vulnerability** suitable for large fault campaigns.

The documented second-stage contributions are:

1. **Hardware-grounded crosstalk fault generator**
   - victims are enumerated from backend topology;
   - triggers are directional and cover 1→1, 1→2, 2→1, 2→2 aggressor/victim arities;
   - error magnitudes are drawn from a discrete RZ set;
   - fault-list coverage becomes deterministic and countable.

2. **Structure-aware simulator Identifier**
   - sparse faults take a prefix-suffix fast path;
   - the Python dispatcher queries structural transition costs from the C++ backend;
   - an iterative deepest-path / nearest-neighbor clustering procedure groups structurally similar faults;
   - clusters are routed among `ps`, `cawst`, and `update_cawst`-style execution paths.

3. **Benchmark study**
   - 7 algorithms: QAOA, QFT, QFT-Entangled, AE, QPE-Exact, QNN, VQE;
   - 10–12 qubits;
   - FakeGuadalupeV2 backend;
   - 45–105 generated crosstalk faults per circuit;
   - runtime, peak memory, and completion/failure behavior compared across engines.

The reported result is not that one simulator always wins; rather, **circuit/fault structure changes which engine is efficient**, motivating structure-aware dispatch.

## Why the two stages belong together

The progression is:

```text
physical / scheduling view
    ↓
spatio-temporal crosstalk model
    ↓
selective software mitigation
    ↓
fault-simulation abstraction
    ↓
reproducible hardware-indexed fault lists
    ↓
structure-aware simulation-engine selection
```

This trajectory moves from modeling and mitigation toward **simulation systems, workload characterization, graph-based routing, and performance-aware execution**—the parts most directly connected to computer science.

## Claim boundaries

- Stage-1 numbers are simulation results on Qiskit fake backends, not live IBM hardware measurements.
- Crosstalk coefficients are model parameters, not device-calibrated constants.
- Stage 2 is documented in the subsequent course paper; its source code is not checked into this repository.
- The second-stage paper explicitly describes the work as a prototype and notes remaining generalization/auto-tuning work.
