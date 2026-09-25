from src.scheduling import Strategy


class DummyModel:
    default_strength = 0.01
    crosstalk_lookup = {("cx", "cx"): 0.12}

    @staticmethod
    def distance_decay(distance):
        return 1.0 if distance == 1 else 0.0

    @staticmethod
    def interaction_distance(qs1, qs2):
        return 1


def gate(oid, qs, dur=100, name="cx"):
    return {
        "oid": oid,
        "name": name,
        "qs": qs,
        "dur": dur,
        "op": None,
        "qubits": (),
    }


def overlap(a, b):
    return max(0, min(a["end"], b["end"]) - max(a["start"], b["start"]))


def test_dense_runs_disjoint_gates_in_parallel():
    s = Strategy()
    ops = [gate(0, [0, 1]), gate(1, [2, 3])]
    out = s.sched_dense(ops, 4)
    assert out[0]["start"] == 0
    assert out[1]["start"] == 0
    assert overlap(out[0], out[1]) == 100


def test_sparse_serializes_all_operations():
    s = Strategy()
    ops = [gate(0, [0, 1]), gate(1, [2, 3])]
    out = s.sched_sparse(ops)
    assert out[0]["start"] == 0
    assert out[1]["start"] == 100
    assert overlap(out[0], out[1]) == 0


def test_offline_staggering_reduces_high_score_overlap():
    s = Strategy()
    m = DummyModel()
    ops = [gate(0, [0, 1]), gate(1, [2, 3])]
    dense = s.sched_dense(ops, 4)
    smart = s.sched_smart_offline(ops, 4, m, threshold=0.02, max_passes=5)
    assert overlap(smart[0], smart[1]) < overlap(dense[0], dense[1])
    assert smart[1]["start"] <= 99


def test_online_cap_is_causal_and_bounded():
    s = Strategy()
    m = DummyModel()
    ops = [gate(0, [0, 1]), gate(1, [2, 3])]
    smart = s.sched_smart_online(ops, 4, m, threshold=0.02, cap_factor=0.8)
    assert smart[0]["start"] == 0
    assert smart[1]["start"] == 80
    assert overlap(smart[0], smart[1]) == 20
