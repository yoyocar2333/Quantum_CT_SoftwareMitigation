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
    model   = UltimateCrosstalkModel(backend=backend, kappa=2.0)
    sim     = AerSimulator(method="density_matrix")
    SEED    = 0
    N       = 5
    LAMBDAS = np.round(np.arange(0, 5.5, 0.5), 2) 

    strategy = Strategy(gap_sparse=2500, gap_smart=800)

    CIRCUITS = [("GHZ", ghz(N)), ("QFT", qft(N)), ("RCS", rcs(N, depth=4, seed=0))]
    STRATS   = ["Dense", "Smart_Offline", "Smart_Online", "Sparse"]

    plt.figure(figsize=(10, 6))

    for cname, cqc in CIRCUITS:
        base = transpile(cqc, backend, optimization_level=1, seed_transpiler=SEED)
        gops = extract(base, model); nq = base.num_qubits
        clean = QuantumCircuit(*base.qregs)
        for g in gops: clean.append(g["op"], g["qubits"])
        ideal_sv = Statevector.from_instruction(clean)

        scheds = {
            "Dense": strategy.sched_dense(gops, nq),
            "Smart_Offline": strategy.sched_smart_offline(gops, nq, model, threshold=0.02),
            "Smart_Online": strategy.sched_smart_online(gops, nq, model, threshold=0.02, cap_factor=0.8),
            "Sparse": strategy.sched_sparse(gops),
        }

        for strat, ops in scheds.items():
            gaps = []
            for lam in LAMBDAS:
                dm = run_noisy(ops, base, model, float(lam), sim)
                sf = state_fidelity(ideal_sv, dm)
                hf = hellinger(ideal_sv, dm)
                gaps.append(sf - hf)

            plt.plot(list(LAMBDAS), gaps, marker="o", label=f"{cname}-{strat}")
        
        print(f"  {cname} done")

    plt.axhline(0, color="k", linestyle="--", alpha=0.4)
    plt.xlabel("Crosstalk Parameter (λ)")
    plt.ylabel("State Fidelity − Hellinger Fidelity")
    plt.title("Information Gap Invisible to Measurement")
    plt.legend(fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run()