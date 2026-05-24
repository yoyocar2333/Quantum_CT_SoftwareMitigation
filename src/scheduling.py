from qiskit import QuantumCircuit

class Strategy:
    def __init__(self, gap_sparse=2500, gap_smart=800):
        self.gap_sparse = gap_sparse
        self.gap_smart = gap_smart

    def dense(self, qc):
        return qc.copy()

    def sparse(self, qc):
        out = QuantumCircuit(qc.num_qubits)
        for inst, qargs, cargs in qc.data:
            out.append(inst, qargs, cargs)
            out.delay(self.gap_sparse, list(range(qc.num_qubits)), unit="dt")
        return out

    def smart(self, qc):
        out = QuantumCircuit(qc.num_qubits)
        for inst, qargs, cargs in qc.data:
            out.append(inst, qargs, cargs)
            if len(qargs) == 2:
                out.delay(self.gap_smart, list(range(qc.num_qubits)), unit="dt")
        return out