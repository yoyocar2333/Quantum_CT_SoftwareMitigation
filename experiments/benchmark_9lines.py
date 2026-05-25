import numpy as np
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crosstalk_model import UltimateCrosstalkModel, extract, pred_total, run_noisy, hellinger
from src.scheduling import Strategy
from src.circuits import ghz, qft, rcs

from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import state_fidelity, Statevector

def run():
    backend = FakeManilaV2()
    model   = UltimateCrosstalkModel(backend=backend)
    sim     = AerSimulator(method="density_matrix")
    SEED    = 0
    N       = 5
    LAMBDAS = np.round(np.arange(0, 5.5, 0.5), 2) 
    TABLE_LAM = 1.0

    strategy = Strategy(gap_sparse=2500, gap_smart=800)

    CIRCUITS = [("GHZ", ghz(N)), ("QFT", qft(N)), ("RCS", rcs(N, depth=4, seed=0))]
    STRATS   = ["Dense", "Smart_Offline", "Smart_Online", "Sparse"]

    results = {}
    curves_H = {f"{c}-{s}": [] for c, _ in CIRCUITS for s in STRATS}
    curves_S = {f"{c}-{s}": [] for c, _ in CIRCUITS for s in STRATS}

    for cname, cqc in CIRCUITS:
        base = transpile(cqc, backend, optimization_level=1, seed_transpiler=SEED)
        gops = extract(base, model); nq = base.num_qubits
        clean = QuantumCircuit(*base.qregs)
        for g in gops: clean.append(g["op"], g["qubits"])
        ideal_sv = Statevector.from_instruction(clean)

        scheds = {
            "Dense": strategy.sched_dense(gops, nq),
            "Smart_Offline": strategy.sched_smart_offline(gops, nq, model, threshold=0.02),
            "Smart_Online": strategy.sched_smart_online(gops, nq, model, threshold=0.02, cap_factor=1.0),
            "Sparse": strategy.sched_sparse(gops),
        }
        base_dur = max(g["end"] for g in scheds["Dense"]) or 1

        for strat, ops in scheds.items():
            dur = max(g["end"] for g in ops)
            key = f"{cname}-{strat}"
            for lam in LAMBDAS:
                dm = run_noisy(ops, base, model, float(lam), sim)
                sf = state_fidelity(ideal_sv, dm)
                hf = hellinger(ideal_sv, dm)
                results[(cname, strat, float(lam))] = {
                    "sf":sf, "hf":hf, "dur":dur, "norm_cost":dur/base_dur}
                curves_H[key].append(hf)
                curves_S[key].append(sf)
        print(f"  {cname} done")

    # Plot Hellinger Fidelity
    plt.figure(figsize=(11, 6))
    for key, vals in curves_H.items():
        plt.plot(list(LAMBDAS), vals, marker="o", label=key)
    plt.xlabel("Crosstalk Parameter (λ)")
    plt.ylabel("Hellinger Fidelity")
    plt.title("Hellinger Fidelity: GHZ/QFT/RCS × Dense/Smart_Offline/Smart_Online/Sparse")
    plt.legend(ncol=3, fontsize=8)
    plt.tight_layout()
    plt.show()

    # Plot State Fidelity
    plt.figure(figsize=(11, 6))
    for key, vals in curves_S.items():
        plt.plot(list(LAMBDAS), vals, marker="s", linestyle="--", label=key)
    plt.xlabel("Crosstalk Parameter (λ)")
    plt.ylabel("State Fidelity")
    plt.title("State Fidelity: GHZ/QFT/RCS × Dense/Smart_Offline/Smart_Online/Sparse")
    plt.legend(ncol=3, fontsize=8)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run()