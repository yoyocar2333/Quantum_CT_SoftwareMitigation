import pandas as pd
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
    backend = FakeManilaV2()
    model = UltimateCrosstalkModel(backend)
    strat = Strategy()

    sim_meas = AerSimulator.from_backend(backend)
    sim_dm = AerSimulator(method="density_matrix", noise_model=NoiseModel.from_backend(backend))

    circuits = {"GHZ": ghz(5), "QFT": qft(5), "RCS": rcs(5)}
    strategies = {"Dense": strat.dense, "Sparse": strat.sparse, "Smart": strat.smart}

    multipliers = [1, 2, 3, 4, 5]
    rows = []

    for cname, qc in circuits.items():
        durations = {}
        for sname, fn in strategies.items():
            base = fn(qc)
            sched = model.transpile_and_schedule(base)
            durations[sname] = int(max(sched.op_start_times) + 1)

        dense_ref = durations["Dense"]

        for sname, fn in strategies.items():
            base = fn(qc)
            sched = model.transpile_and_schedule(base)

            base_dm = sched.copy()
            base_dm.save_density_matrix()
            rho0 = sim_dm.run(base_dm).result().data(0)["density_matrix"]

            base_meas = sched.copy()
            base_meas.measure_all()
            p0 = sim_meas.run(base_meas, shots=10000).result().get_counts()

            for m in multipliers:
                ct = model.inject(sched, m)
                ct_dm = ct.copy()
                ct_dm.save_density_matrix()
                rho = sim_dm.run(ct_dm).result().data(0)["density_matrix"]

                ct_meas = ct.copy()
                ct_meas.measure_all()
                p = sim_meas.run(ct_meas, shots=10000).result().get_counts()

                rows.append({
                    "Circuit": cname,
                    "Strategy": sname,
                    "Multiplier": m,
                    "Hellinger": hellinger_fidelity(p0, p),
                    "StateFidelity": state_fidelity(rho0, rho),
                    "Duration(dt)": durations[sname],
                    "NormCost": durations[sname] / dense_ref,
                })

    df = pd.DataFrame(rows)
    print("\n=== Final Normalized Cost Table ===")
    print(df)

if __name__ == "__main__":
    run()