from qiskit import QuantumCircuit

class Strategy:
    def __init__(self, gap_sparse=2500, gap_smart=800):
        self.gap_sparse = gap_sparse
        self.gap_smart = gap_smart

    def sched_dense(gops,nq):
        free=[0]*nq; out=[]
        for g in gops:
            st=max(free[q] for q in g["qs"]); e=st+g["dur"]
            for q in g["qs"]: free[q]=e
            out.append({**g,"start":st,"end":e})
        return out
    
    def sched_sparse(gops):
        t=0; out=[]
        for g in gops:
            out.append({**g,"start":t,"end":t+g["dur"]}); t+=g["dur"]
        return out
    
    def sched_smart_offline(gops,nq,model,threshold=0.02):
        d=sched_dense(gops,nq); dly={}
        for i in range(len(d)):
            for j in range(i+1,len(d)):
                a,b=d[i],d[j]
                decay=model.distance_decay(model.interaction_distance(a["qs"],b["qs"]))
                if decay<1e-3: continue
                ov=min(a["end"],b["end"])-max(a["start"],b["start"])
                if ov<=0: continue
                if base_strength(a["name"],b["name"],model)*decay*(ov/min(a["dur"],b["dur"]))<threshold: continue
                agg,vic=(a,b) if (a["start"],len(a["qs"]))<=(b["start"],len(b["qs"])) else (b,a)
                need=int(min(ov,agg["dur"]-1))
                if need>0: dly[vic["oid"]]=max(dly.get(vic["oid"],0),need)
        free=[0]*nq; out=[]
        for g in gops:
            st=max(free[q] for q in g["qs"])+dly.get(g["oid"],0); e=st+g["dur"]
            for q in g["qs"]: free[q]=e
            out.append({**g,"start":st,"end":e})
        return out
    
    def sched_smart_online(gops,nq,model,threshold=0.02,cap_factor=1.0):
        free=[0]*nq; active=[]; out=[]
        for g in gops:
            earliest=max(free[q] for q in g["qs"])
            active=[a for a in active if a["end"]>earliest]
            best,tend=0.0,earliest
            for a in active:
                decay=model.distance_decay(model.interaction_distance(a["qs"],g["qs"]))
                if decay<1e-3: continue
                ov=a["end"]-earliest
                if ov<=0: continue
                sc=base_strength(a["name"],g["name"],model)*decay*(ov/g["dur"])
                if sc>best: best,tend=sc,a["end"]
            delay=int(min(max(tend-earliest,0),int(cap_factor*g["dur"]))) if best>=threshold else 0
            st=earliest+delay; e=st+g["dur"]
            for q in g["qs"]: free[q]=e
            active.append({"qs":g["qs"],"name":g["name"],"end":e})
            out.append({**g,"start":st,"end":e})
        return out
    
