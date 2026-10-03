"""
Correct cost analysis for deliberately stopping Grover before the first maximum.

A shorter run is not automatically cheaper.  If one run succeeds with
probability p(k), repeat it enough times to obtain a fixed overall target
success probability eta.

R(k) = ceil(log(1-eta) / log(1-p(k)))
cost(k) = R(k) * k

The oracle/diffuser cost factor is common, so this script compares query
iterations first; an optional per-iteration T count converts to logical T cost.
"""

import math,csv
from partial_key_grover import closed_form_success

def repeats_for_target(p,eta=0.99):
    if p >= eta:
        return 1
    if p <= 0:
        return math.inf
    return math.ceil(math.log(1-eta)/math.log(1-p))

def analyze(N,M,eta=0.99,max_k=None,per_iteration_T=None):
    theta=math.asin(math.sqrt(M/N))
    if max_k is None:
        max_k=max(1,int(math.ceil(math.pi/(4*theta))))
    rows=[]
    for k in range(1,max_k+1):
        p=closed_form_success(N,M,k)
        R=repeats_for_target(p,eta)
        q=R*k
        row={
            "iterations_per_run":k,
            "success_per_run":p,
            "repetitions_for_target":R,
            "total_Grover_iterations":q,
        }
        if per_iteration_T is not None:
            row["total_naive_T"]=q*per_iteration_T
        rows.append(row)
    return rows

if __name__=="__main__":
    N=256; M=1; eta=0.99
    rows=analyze(N,M,eta,per_iteration_T=76986)
    best=min(rows,key=lambda r:r["total_Grover_iterations"])
    print("N =",N,"M =",M,"target overall success =",eta)
    print("best fixed-success query cost:")
    print(best)
    with open("EARLY_STOP_TRADEOFF.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
