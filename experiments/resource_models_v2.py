"""Second fault-tolerant resource model and depth-oriented oracle comparison.

Two exact-Toffoli decomposition models are reported:

FT-A (width-oriented): 7 T per CCX, T-depth 3, no decomposition ancilla.
FT-B (depth-oriented): 7 T per CCX, T-depth 1, 4 clean ancillas per
simultaneously scheduled CCX (Selinger-style depth-1 Toffoli model).

The circuit's CCX-layer depth is computed with a dependency-aware ASAP pass.
Clifford gates add no T layer but propagate dependencies between their wires.
Thus:
  Tdepth_A = 3 * CCX_layer_depth
  Tdepth_B = 1 * CCX_layer_depth
and the conservative extra width for FT-B is 4 * peak_parallel_CCX.
"""

from collections import Counter, defaultdict
import csv

from warp_quantum_round import build_full_encryption
from grover_oracle import two_pair_wide_iteration
from depth_optimized_oracle import (
    two_pair_wide_balanced_iteration,
    two_pair_parallel_balanced_iteration,
)


def wires(g):
    return list(g[1:])


def gate_counts(gates):
    return Counter(g[0] for g in gates)


def weighted_depth(gates, nq):
    wt = {"X":1,"H":1,"Z":1,"CX":1,"CZ":1,"CCX":7}
    d=[0]*nq
    for g in gates:
        ws=wires(g)
        t=max((d[q] for q in ws),default=0)+wt[g[0]]
        for q in ws: d[q]=t
    return max(d)


def ccx_layer_schedule(gates, nq):
    """Return CCX-layer depth, peak CCX parallelism, and per-layer counts.

    Clifford gates have zero T-cost but synchronize the T-layer dependency
    labels of all wires they touch. CCX increments the maximum incoming label.
    """
    d=[0]*nq
    layers=defaultdict(int)
    for g in gates:
        ws=wires(g)
        if g[0]=="CCX":
            t=max(d[q] for q in ws)+1
            layers[t]+=1
            for q in ws: d[q]=t
        else:
            t=max((d[q] for q in ws),default=0)
            for q in ws: d[q]=t
    depth=max(d) if d else 0
    peak=max(layers.values(), default=0)
    return depth,peak,dict(sorted(layers.items()))


def summarize(name,gates,nq):
    c=gate_counts(gates)
    td,peak,_=ccx_layer_schedule(gates,nq)
    return {
        "construction":name,
        "logical_qubits":nq,
        "CCX":c["CCX"],
        "T_count_FT_A_or_B":7*c["CCX"],
        "CCX_layer_depth":td,
        "T_depth_FT_A_no_ancilla":3*td,
        "T_depth_FT_B_depth1":td,
        "peak_parallel_CCX":peak,
        "extra_qubits_FT_B_upper":4*peak,
        "width_FT_B_upper":nq+4*peak,
        "weighted_NCT_depth":weighted_depth(gates,nq),
        "total_logical_gates":len(gates),
    }


def main():
    eg, _ = build_full_encryption()
    entries=[("WARP encryption",eg,256)]
    for name,builder in [
        ("two-pair ladder iteration",two_pair_wide_iteration),
        ("two-pair balanced iteration",two_pair_wide_balanced_iteration),
        ("two-pair parallel+balanced iteration",two_pair_parallel_balanced_iteration),
    ]:
        g,nq=builder(); entries.append((name,g,nq))

    rows=[summarize(n,g,q) for n,g,q in entries]
    with open("RESOURCE_MODELS_V2.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    for r in rows: print(r)

if __name__=="__main__":
    main()
