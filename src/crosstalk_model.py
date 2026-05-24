import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer.noise.errors import depolarizing_error, coherent_unitary_error
from qiskit.quantum_info import Operator
from qiskit.circuit.library import QFTGate, RZGate

from src.scheduling import base_strength

class UltimateCrosstalkModel:
    def __init__(self, backend, crosstalk_lookup=None, default_strength=0.01, kappa=1.5, include_phase_error=True, seed_transpiler=11, opt_level=1):
        self.backend=backend
        self.coupling=backend.coupling_map
        self.default_strength = default_strength; self.kappa=kappa
        self.include_phase_error = include_phase_error
        self._durations = backend.instruction_durations
        self.seed_transpiler = seed_transpiler; self.opt_level=opt_level
        self.crosstalk_lookup = crosstalk_lookup or {('cx','x'):0.08,('x','cx'):0.02,
                                                   ('cx','cx'):0.12,('x','x'):0.01}
    def distance_decay(self,d):
        return 0.0 if (d<1 or d>3) else float(np.exp(-self.kappa*(d-1)))
    def interaction_distance(self,qs1,qs2):
        dmin=np.inf
        for q1 in qs1:
            for q2 in qs2:
                if q1==q2: continue
                try:
                    d=self.coupling.distance(q1,q2)
                    if d<dmin: dmin=d
                except: pass
        return dmin if dmin!=np.inf else 999
    def _duration_dt(self,name,qubits):
        try:
            d=self._durations.get(name,qubits,unit="dt")
            if d is not None: return int(d)
        except: pass
        return 160
    def create_error_instruction(self,p,nq):
        err=depolarizing_error(min(p,1.0),nq)
        if self.include_phase_error and p>0.001:
            u=Operator(RZGate(p*np.pi*0.5))
            if nq>1: u=u.tensor(Operator(np.eye(2)))
            err=err.compose(coherent_unitary_error(u))
        return err.to_instruction()

def extract(base, model):
    gops=[]; oid=0
    for ci in base.data:
        op=ci.operation
        if op.name in ("barrier","measure","reset","delay"): continue
        qs=[base.find_bit(q).index for q in ci.qubits]
        gops.append({"oid":oid,"name":op.name,"qs":qs,"qubits":ci.qubits,
                     "op":op,"dur":max(model._duration_dt(op.name,qs), 1)})
        oid+=1                                     
    return gops

def pred_total(ops,model):
    tot=0.0
    for i in range(len(ops)):
        for j in range(i+1,len(ops)):
            a,b=ops[i],ops[j]
            decay=model.distance_decay(model.interaction_distance(a["qs"],b["qs"]))
            if decay<1e-3: continue
            ov=min(a["end"],b["end"])-max(a["start"],b["start"])
            if ov<=0: continue
            tot+=base_strength(a["name"],b["name"],model)*decay*(ov/min(a["dur"],b["dur"]))
    return tot

def run_noisy(ops, base, model, lam, sim):
    p = {}
    for i in range(len(ops)):
        for j in range(i+1, len(ops)):
            a,b = ops[i],ops[j]
            decay = model.distance_decay(model.interaction_distance(a["qs"],b["qs"]))
            if decay < 1e-3: continue
            ov = min(a["end"],b["end"]) - max(a["start"],b["start"])
            if ov <= 0: continue
            pba = model.crosstalk_lookup.get((b["name"],a["name"]),model.default_strength)*decay*(ov/a["dur"])*lam
            if pba>1e-6: p.setdefault(a["oid"],[]).append(pba)
            pab = model.crosstalk_lookup.get((a["name"],b["name"]),model.default_strength)*decay*(ov/b["dur"])*lam
            if pab>1e-6: p.setdefault(b["oid"],[]).append(pab)
    nqc = QuantumCircuit(*base.qregs, *base.cregs)
    for it in sorted(ops, key=lambda x: x["oid"]):
        nqc.append(it["op"], it["qubits"])
        if it["oid" ] in p:
            ptot = 1.0 - np.prod([1-x for x in p[it["oid"]]])
            nqc.append(model.create_error_instruction(ptot,len(it["qubits"])), it["qubits"])
    nqc.save_density_matrix()
    dm = sim.run(nqc).result().data()["density_matrix"]
    return dm

def hellinger(ideal_sv, noisy_dm):
    p_i = np.abs(ideal_sv.data)**2
    p_n = np.maximum(np.real(np.diag(noisy_dm.data)), 0)
    return float(np.sum(np.sqrt(p_i * p_n))**2)
