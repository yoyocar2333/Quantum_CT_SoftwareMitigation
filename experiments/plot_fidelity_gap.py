import numpy as np
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crosstalk_model import UltimateCrosstalkModel
from src.scheduling import Strategy
from src.circuits import ghz, qft, rcs

from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit.quantum_info import hellinger_fidelity, state_fidelity
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

def run_gap_9lines():
    backend = FakeManilaV2()
    model = UltimateCrosstalkModel(backend)
    strat = Strategy()

    sim_meas = AerSimulator.from_backend(backend)
    sim_dm = AerSimulator(method="density_matrix", noise_model=NoiseModel.from_backend(backend))

    circuits = {"GHZ": ghz(5), "QFT": qft(5), "RCS": rcs(5)}
    strategies = {"Dense": strat.dense, "Sparse": strat.sparse, "Smart": strat.smart}
    multipliers = [0, 1, 2, 3, 4, 5]

    plt.figure(figsize=(10, 6))

    for cname, qc in circuits.items():
        for sname, fn in strategies.items():
            base = fn(qc)
            sched = model.transpile_and_schedule(base)

            dm0 = sched.copy()
            dm0.save_density_matrix()
            rho0 = sim_dm.run(dm0).result().data(0)["density_matrix"]

            m0 = sched.copy()
            m0.measure_all()
            p0 = sim_meas.run(m0, shots=10000).result().get_counts()

            gaps = []
            for m in multipliers:
                if m == 0:
                    rho, p = rho0, p0
                else:
                    ct = model.inject(sched, m)
                    dm = ct.copy()
                    dm.save_density_matrix()
                    rho = sim_dm.run(dm).result().data(0)["density_matrix"]

                    meas = ct.copy()
                    meas.measure_all()
                    p = sim_meas.run(meas, shots=10000).result().get_counts()

                gaps.append(state_fidelity(rho0, rho) - hellinger_fidelity(p0, p))

            plt.plot(multipliers, gaps, marker="o", label=f"{cname}-{sname}")

    plt.axhline(0, color="k", linestyle="--", alpha=0.4)
    plt.xlabel("Crosstalk Multiplier")
    plt.ylabel("State − Hellinger Fidelity")
    plt.title("Information Gap Invisible to Measurement")
    plt.legend(fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_gap_9lines()