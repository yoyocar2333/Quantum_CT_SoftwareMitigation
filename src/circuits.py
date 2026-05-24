import numpy as np
import random
from qiskit import QuantumCircuit

def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    return qc

def qft(n):
    qc = QuantumCircuit(n)
    for j in range(n):
        qc.h(j)
        for k in range(j + 1, n):
            qc.cp(np.pi / (2 ** (k - j)), k, j)
    return qc

def rcs(n, depth=4, seed=0):
    rnd = random.Random(seed)
    qc = QuantumCircuit(n)
    for _ in range(depth):
        for q in range(n):
            getattr(qc, rnd.choice(["x", "h"]))(q)
        for q in range(0, n - 1, 2):
            qc.cx(q, q + 1)
    return qc