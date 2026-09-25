class Strategy:
    def __init__(self, gap_sparse=2500, gap_smart=800):
        self.gap_sparse = gap_sparse
        self.gap_smart = gap_smart

    def sched_dense(self, gops, nq):
        free = [0] * nq
        out = []
        for g in gops:
            st = max(free[q] for q in g["qs"])
            e = st + g["dur"]
            for q in g["qs"]:
                free[q] = e
            out.append({**g, "start": st, "end": e})
        return out

    def sched_sparse(self, gops):
        t = 0
        out = []
        for g in gops:
            out.append({**g, "start": t, "end": t + g["dur"]})
            t += g["dur"]
        return out

    def _schedule_with_delays(self, gops, nq, delays):
        """Schedule in program order with per-operation delay budgets."""
        free = [0] * nq
        out = []
        for g in gops:
            st = max(free[q] for q in g["qs"]) + delays.get(g["oid"], 0)
            e = st + g["dur"]
            for q in g["qs"]:
                free[q] = e
            out.append({**g, "start": st, "end": e})
        return out

    def sched_smart_offline(self, gops, nq, model, threshold=0.02, max_passes=5):
        """Iterative global overlap reduction with bounded per-victim delays."""
        delays = {}

        for _ in range(max_passes):
            scheduled = self._schedule_with_delays(gops, nq, delays)
            changed = False

            for i in range(len(scheduled)):
                for j in range(i + 1, len(scheduled)):
                    a, b = scheduled[i], scheduled[j]
                    decay = model.distance_decay(
                        model.interaction_distance(a["qs"], b["qs"])
                    )
                    if decay < 1e-3:
                        continue

                    overlap = min(a["end"], b["end"]) - max(a["start"], b["start"])
                    if overlap <= 0:
                        continue

                    score = (
                        base_strength(a["name"], b["name"], model)
                        * decay
                        * (overlap / min(a["dur"], b["dur"]))
                    )
                    if score < threshold:
                        continue

                    aggressor, victim = (
                        (a, b)
                        if (a["start"], len(a["qs"])) <= (b["start"], len(b["qs"]))
                        else (b, a)
                    )

                    cap = max(int(aggressor["dur"]) - 1, 0)
                    used = delays.get(victim["oid"], 0)
                    room = max(cap - used, 0)
                    add = int(min(overlap, room))
                    if add > 0:
                        delays[victim["oid"]] = used + add
                        changed = True

            if not changed:
                break

        return self._schedule_with_delays(gops, nq, delays)

    def sched_smart_online(self, gops, nq, model, threshold=0.02, cap_factor=0.8):
        """Causal scheduler using only already-scheduled active gates."""
        free = [0] * nq
        active = []
        out = []

        for g in gops:
            earliest = max(free[q] for q in g["qs"])
            active = [a for a in active if a["end"] > earliest]

            best = 0.0
            target_end = earliest
            for a in active:
                decay = model.distance_decay(
                    model.interaction_distance(a["qs"], g["qs"])
                )
                if decay < 1e-3:
                    continue

                overlap = a["end"] - earliest
                if overlap <= 0:
                    continue

                score = (
                    base_strength(a["name"], g["name"], model)
                    * decay
                    * (overlap / g["dur"])
                )
                if score > best:
                    best, target_end = score, a["end"]

            delay = 0
            if best >= threshold:
                delay = int(
                    min(
                        max(target_end - earliest, 0),
                        int(cap_factor * g["dur"]),
                    )
                )

            st = earliest + delay
            e = st + g["dur"]
            for q in g["qs"]:
                free[q] = e

            active.append({"qs": g["qs"], "name": g["name"], "end": e})
            out.append({**g, "start": st, "end": e})

        return out


def base_strength(a, b, model):
    return max(
        model.crosstalk_lookup.get((a, b), model.default_strength),
        model.crosstalk_lookup.get((b, a), model.default_strength),
    )
