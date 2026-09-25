# Spatio-Temporal Modeling and Software-Based Mitigation of Crosstalk in Quantum Computing

Research prototype for modeling **time-dependent, topology-aware crosstalk** in NISQ circuits and mitigating it through software scheduling.

The compiler-level question is simple: dense scheduling reduces latency but increases simultaneous-gate crosstalk; full serialization avoids overlap but is expensive. **Smart Staggering** inserts delays only when the model predicts harmful overlap.


## Research trajectory

This repository is the first stage of a two-stage undergraduate research trajectory:

1. **Spatio-temporal crosstalk modeling + Smart Staggering** — model coherent, topology- and overlap-dependent crosstalk and study the fidelity/latency trade-off of selective delay insertion.
2. **Decision-diagram fault simulation + structure-aware dispatch** — a subsequent course project reframes crosstalk as a hardware-indexed, reproducible fault source for DDFSIM and studies simulator selection across 7 algorithms at 10–12 qubits.

The continuation is summarized in [`docs/CONTINUATION_DDFSIM.md`](docs/CONTINUATION_DDFSIM.md). It is documented separately because the second-stage DDFSIM source is not part of this repository.

## Contributions

### 1. Spatio-temporal crosstalk model

The model combines:

- **hardware topology** — interaction strength decays with coupling-map distance;
- **temporal overlap** — only concurrently active operations interact;
- **asymmetric gate dependence** — CX→X, X→CX, CX→CX and X→X use different coefficients;
- **coherent phase error** — an RZ-type unitary component exposes phase damage that measurement-only metrics can miss;
- **probabilistic merging** — multiple aggressors on one victim are merged rather than naively summed.

The global multiplier `λ` is an **experimental sweep variable**, not a calibrated hardware constant.

### 2. Four scheduling strategies

| Strategy | Behavior |
|---|---|
| Dense | ASAP-style baseline; maximize parallelism |
| Sparse | Fully serialize operations |
| Smart Offline | Global iterative overlap reduction, up to 5 refinement passes |
| Smart Online | Causal/no-lookahead scheduling; delay capped at 0.8× victim duration |

### 3. State fidelity vs. measurement fidelity

The experiments compare **state fidelity** with **Hellinger fidelity**. This exposes cases where computational-basis measurement distributions remain similar even though coherent phase information has degraded.

## Paper-reported results

The accompanying NTU Electrical Engineering course paper evaluates GHZ, QFT, and depth-4 RCS on a simulated IBM FakeManilaV2 backend. At `λ = 1`:

| Circuit | Strategy | Hellinger | State fidelity | Duration (dt) | Norm. cost |
|---|---|---:|---:|---:|---:|
| GHZ | all four | 1.0000 | 1.0000 | 6624 | 1.00× |
| QFT | Dense | 1.0000 | 0.1668 | 52736 | 1.00× |
| QFT | Smart Offline | 1.0000 | **0.6910** | 61947 | 1.17× |
| QFT | Smart Online | 1.0000 | 0.4834 | 59390 | 1.13× |
| QFT | Sparse | 1.0000 | 1.0000 | 65312 | 1.24× |
| RCS | Dense | 0.5761 | 0.4885 | 7040 | 1.00× |
| RCS | Smart Offline | 0.8434 | **0.8028** | 11421 | 1.62× |
| RCS | Smart Online | 0.8079 | 0.7374 | 10226 | 1.45× |
| RCS | Sparse | 1.0000 | 1.0000 | 14112 | 2.00× |

Headline results from the report:

- QFT state fidelity improves **4.1×**, from 0.1668 to 0.6910, at 1.17× latency with Smart Offline.
- RCS improves from 0.4885 to 0.8028 at 1.62× latency, versus 2.00× for full serialization.

These are **simulation results from the course paper**, not measurements from physical IBM hardware.

## Repository structure

```text
.
├── src/
│   ├── circuits.py
│   ├── crosstalk_model.py
│   └── scheduling.py
├── experiments/
│   ├── benchmark_9lines.py
│   ├── benchmark_norm_cost.py
│   └── plot_fidelity_gap.py
└── tests/
    └── test_scheduling.py
```

## Reproduce

Python 3.10+ is recommended.

```bash
git clone https://github.com/yoyocar2333/Quantum_CT_SoftwareMitigation.git
cd Quantum_CT_SoftwareMitigation
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python experiments/benchmark_norm_cost.py
python experiments/benchmark_9lines.py
python experiments/plot_fidelity_gap.py
```

The checked-in experiment scripts now explicitly use the paper configuration `κ = 2.0`, Smart threshold `0.02`, at most five offline refinement passes, and an online delay cap of `0.8×`.

Scheduler regression tests are intentionally hardware-free:

```bash
pip install pytest
pytest -q
```

## Research limitations

This is a **course-project research prototype**. The crosstalk coefficients are model parameters rather than device-calibrated constants, the evaluation uses FakeManilaV2 rather than live hardware, and the benchmark set is small. The goal is to study the scheduling/fidelity trade-off under a controlled correlated-noise model, not to claim hardware-calibrated error prediction.

## Research continuation

A subsequent project extends this direction toward **decision-diagram fault simulation**, hardware-topology-derived crosstalk fault generation, and structure-aware simulator dispatch across 10–12-qubit workloads.
