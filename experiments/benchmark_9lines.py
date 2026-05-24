import numpy as np
import pandas as pd
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

def run():
    shots = 10000
    multipliers = [0, 1, 2, 3, 4, 5]
    backend = FakeManilaV2()
    
    model = UltimateCrosstalkModel(backend)
    strat = Strategy()
    sim_meas = AerSimulator.from_backend(backend)
    sim_dm = AerSimulator(method="density_matrix", noise_model=NoiseModel.from_backend(backend))

    circuits = {"GHZ": ghz(5), "QFT": qft(5), "RCS": rcs(5)}
    strategies = {"Dense": strat.dense, "Sparse": strat.sparse, "Smart": strat.smart}

    curves_H = {}
    curves_S = {}
    summary_rows = []

    for cname, qc in circuits.items():
        dense_duration_ref = None
        for sname, fn in strategies.items():
            base = fn(qc)
            sched = model.transpile_and_schedule(base)
            
            duration_dt = int(max(sched.op_start_times)) if len(sched.op_start_times) else 0
            if sname == "Dense":
                dense_duration_ref = max(duration_dt, 1)

            base_dm = sched.copy()
            base_dm.save_density_matrix()
            rho0 = sim_dm.run(base_dm).result().data(0)["density_matrix"]

            base_meas = sched.copy()
            base_meas.measure_all()
            p0 = sim_meas.run(base_meas, shots=shots).result().get_counts()

            key = f"{cname}-{sname}"
            curves_H[key] = []
            curves_S[key] = []

            for m in multipliers:
                if m == 0:
                    rho, p = rho0, p0
                else:
                    ct = model.inject(sched, m)
                    ct_dm = ct.copy()
                    ct_dm.save_density_matrix()
                    rho = sim_dm.run(ct_dm).result().data(0)["density_matrix"]

                    ct_meas = ct.copy()
                    ct_meas.measure_all()
                    p = sim_meas.run(ct_meas, shots=shots).result().get_counts()

                curves_H[key].append(hellinger_fidelity(p0, p))
                curves_S[key].append(state_fidelity(rho0, rho))

            avgH = float(np.mean(curves_H[key]))
            avgS = float(np.mean(curves_S[key]))
            summary_rows.append({
                "Circuit": cname,
                "Strategy": sname,
                "AvgHellinger": avgH,
                "AvgStateFidelity": avgS,
                "Duration_dt": duration_dt,
                "NormCost": duration_dt / dense_duration_ref if dense_duration_ref else np.nan,
            })

    # Plot
    plt.figure(figsize=(11, 6))
    for key, vals in curves_H.items():
        plt.plot(list(multipliers), vals, marker="o", label=key)
    plt.xlabel("Crosstalk Multiplier")
    plt.ylabel("Hellinger Fidelity")
    plt.title("Hellinger Fidelity: GHZ/QFT/RCS × Dense/Sparse/Smart")
    plt.legend(ncol=3, fontsize=8)
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(11, 6))
    for key, vals in curves_S.items():
        plt.plot(list(multipliers), vals, marker="s", linestyle="--", label=key)
    plt.xlabel("Crosstalk Multiplier")
    plt.ylabel("State Fidelity")
    plt.title("State Fidelity: GHZ/QFT/RCS × Dense/Sparse/Smart")
    plt.legend(ncol=3, fontsize=8)
    plt.tight_layout()
    plt.show()

    df = pd.DataFrame(summary_rows)
    print(df.to_string(index=False))

if __name__ == "__main__":
    run()