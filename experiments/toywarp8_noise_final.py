#!/usr/bin/env python3
"""Final replicated Toy-WARP-8 Qiskit/Aer depolarizing-noise campaign."""

import csv, math
from pathlib import Path
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from toywarp8_qiskit_end_to_end import build

OUT=Path(__file__).resolve().parents[1]/"data"/"toywarp8"
OUT.mkdir(parents=True,exist_ok=True)

SHOTS=4096
SIM_SEEDS=[101,202,303]
TRANSPILE_SEED=777
ITERATIONS=[3,6,9,12]
SCENARIOS=[
    ("ideal",0.0,0.0),
    ("mild",1e-5,1e-4),
    ("strong",1e-4,1e-3),
]
TRUE_KEY_BITS="11000110"
BASIS=["rz","sx","x","cx"]

def wilson(correct,n,z=1.959963984540054):
    ph=correct/n
    den=1+z*z/n
    cen=(ph+z*z/(2*n))/den
    rad=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    return cen-rad,cen+rad

def r99(p):
    if p>=0.99:
        return 1
    return math.ceil(math.log(0.01)/math.log(1-p))

def noise_model(p1,p2):
    nm=NoiseModel()
    if p1>0:
        err1=depolarizing_error(p1,1)
        nm.add_all_qubit_quantum_error(err1,["x","sx"])
    if p2>0:
        err2=depolarizing_error(p2,2)
        nm.add_all_qubit_quantum_error(err2,["cx"])
    return nm

def main():
    # Compile each j-point exactly once and reuse it for all scenarios/seeds.
    compiled={}
    for j in ITERATIONS:
        qc=build(iterations=j)
        compiled[j]=transpile(
            qc,
            basis_gates=BASIS,
            optimization_level=1,
            seed_transpiler=TRANSPILE_SEED,
        )
        print("compiled",j,"depth",compiled[j].depth())

    raw=[]
    for scenario,p1,p2 in SCENARIOS:
        nm=noise_model(p1,p2)
        for j in ITERATIONS:
            tqc=compiled[j]
            for seed in SIM_SEEDS:
                sim=AerSimulator(method="statevector",noise_model=nm)
                result=sim.run(tqc,shots=SHOTS,seed_simulator=seed).result()
                counts=result.get_counts()
                correct=counts.get(TRUE_KEY_BITS,0)
                raw.append({
                    "scenario":scenario,
                    "p1":p1,
                    "p2":p2,
                    "iterations":j,
                    "seed":seed,
                    "correct":correct,
                    "shots":SHOTS,
                    "success":correct/SHOTS,
                    "depth":tqc.depth(),
                })
                print(raw[-1])

    raw_path=OUT/"QISKIT_NOISE_FINAL_RAW.csv"
    with raw_path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=raw[0].keys())
        w.writeheader(); w.writerows(raw)

    summary=[]
    for scenario,p1,p2 in SCENARIOS:
        for j in ITERATIONS:
            rr=[x for x in raw if x["scenario"]==scenario and x["iterations"]==j]
            correct=sum(x["correct"] for x in rr)
            n=sum(x["shots"] for x in rr)
            p=correct/n
            lo,hi=wilson(correct,n)
            R=r99(p)
            summary.append({
                "scenario":scenario,
                "p1":p1,
                "p2":p2,
                "iterations":j,
                "replicates":";".join(f'{x["success"]:.12f}' for x in rr),
                "pooled_success":p,
                "wilson95_low":lo,
                "wilson95_high":hi,
                "R99":R,
                "total_iter_99":j*R,
                "depth":rr[0]["depth"],
            })

    with (OUT/"QISKIT_NOISE_FINAL_SUMMARY.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=summary[0].keys())
        w.writeheader(); w.writerows(summary)

    (OUT/"QISKIT_NOISE_FINAL_METADATA.txt").write_text(
        "Toy-WARP-8 final Qiskit/Aer replicated noise campaign\n"
        f"shots_per_seed = {SHOTS}\n"
        f"simulator_seeds = {SIM_SEEDS}\n"
        f"fixed_transpiler_seed = {TRANSPILE_SEED}\n"
        f"iterations = {ITERATIONS}\n"
        f"scenarios = {SCENARIOS}\n"
        f"true_key_bits = {TRUE_KEY_BITS}\n"
        f"basis_gates = {BASIS}\n"
        "optimization_level = 1\n"
        "RZ is virtual/noiseless; X/SX and CX receive the declared depolarizing errors.\n"
    )

if __name__=="__main__":
    main()
