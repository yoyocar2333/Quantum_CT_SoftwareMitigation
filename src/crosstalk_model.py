import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer.noise.errors import depolarizing_error, coherent_unitary_error
from qiskit.quantum_info import Operator

class UltimateCrosstalkModel:
    def __init__(self, backend, kappa=2.0, include_phase_error=True, seed_transpiler=11, opt_level=1):
        self.backend = backend
        self.coupling = backend.coupling_map
        self.kappa = kappa
        self.include_phase_error = include_phase_error
        self.seed_transpiler = seed_transpiler
        self.opt_level = opt_level
        self._durations = backend.instruction_durations

        # Asymmetric CT table (CX / X)
        self.ct_table = {
            ("cx", "cx"): 0.12,
            ("cx", "x"): 0.08,
            ("x", "cx"): 0.02,
            ("x", "x"): 0.01,
        }

    def transpile_and_schedule(self, qc):
        return transpile(
            qc,
            self.backend,
            scheduling_method="asap",
            optimization_level=self.opt_level,
            seed_transpiler=self.seed_transpiler,
        )

    def _duration_dt(self, name, qubits):
        try:
            d = self._durations.get(name, qubits, unit="dt")
            if d is not None:
                return int(d)
        except Exception:
            pass
        return 160

    def distance_decay(self, d):
        if d < 1 or d > 3:
            return 0.0
        return np.exp(-self.kappa * (d - 1))

    def zz_phase_error(self, theta):
        U = np.diag([
            np.exp(-1j * theta),
            np.exp(+1j * theta),
            np.exp(+1j * theta),
            np.exp(-1j * theta),
        ])
        return coherent_unitary_error(Operator(U))

    def inject(self, tqc, multiplier):
        insts = tqc.data
        starts = tqc.op_start_times
        ops = []
        
        for idx, ci in enumerate(insts):
            if ci.operation.name in ["measure", "barrier", "delay"]:
                continue
            phys = [tqc.find_bit(q).index for q in ci.qubits]
            ops.append({
                "idx": idx,
                "start": int(starts[idx]),
                "end": int(starts[idx]) + self._duration_dt(ci.operation.name, phys),
                "dur": self._duration_dt(ci.operation.name, phys),
                "phys": phys,
                "name": ci.operation.name,
                "qubits": ci.qubits,
            })

        p_victim = {}

        for i in range(len(ops)):
            for j in range(i + 1, len(ops)):
                A, B = ops[i], ops[j]
                try:
                    d = min(self.coupling.distance(x, y) for x in A["phys"] for y in B["phys"] if x != y)
                except ValueError:
                    continue

                decay = self.distance_decay(d)
                if decay == 0:
                    continue

                overlap = min(A["end"], B["end"]) - max(A["start"], B["start"])
                if overlap <= 0:
                    continue

                p_ab = self.ct_table.get((A["name"], B["name"]), 0.0) * decay * overlap / A["dur"] * multiplier
                p_ba = self.ct_table.get((B["name"], A["name"]), 0.0) * decay * overlap / B["dur"] * multiplier

                if p_ab > 0:
                    p_victim.setdefault(B["idx"], []).append(p_ab)
                if p_ba > 0:
                    p_victim.setdefault(A["idx"], []).append(p_ba)

        new_qc = QuantumCircuit(*tqc.qregs)
        for idx, ci in enumerate(insts):
            new_qc.append(ci)
            if idx in p_victim:
                p = 1 - np.prod([1 - min(x, 1.0) for x in p_victim[idx]])
                err = depolarizing_error(p, len(ci.qubits))
                if self.include_phase_error and len(ci.qubits) == 2:
                    err = err.compose(self.zz_phase_error(0.5 * np.pi * p))
                new_qc.append(err.to_instruction(), ci.qubits)

        return new_qc