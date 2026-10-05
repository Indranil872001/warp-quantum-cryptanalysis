#!/usr/bin/env python3
"""Regenerate the Toy-WARP-8 noise figure from the final summary CSV."""

import csv, math
from pathlib import Path
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"toywarp8"/"QISKIT_NOISE_FINAL_SUMMARY.csv"
OUT=ROOT/"data"/"toywarp8"/"toywarp8_qiskit_noise_final.pdf"

rows=list(csv.DictReader(DATA.open()))
labels={
    "ideal":"Zero-noise simulator",
    "mild":"Mild depolarizing",
    "strong":"Strong depolarizing",
}

fig,ax=plt.subplots(figsize=(7.6,4.6))
for scenario in ("ideal","mild","strong"):
    rr=sorted((r for r in rows if r["scenario"]==scenario),key=lambda r:int(r["iterations"]))
    xs=[int(r["iterations"]) for r in rr]
    ys=[float(r["pooled_success"]) for r in rr]
    lo=[y-float(r["wilson95_low"]) for y,r in zip(ys,rr)]
    hi=[float(r["wilson95_high"])-y for y,r in zip(ys,rr)]
    ax.errorbar(xs,ys,yerr=[lo,hi],marker="o",capsize=3,label=labels[scenario])

theta=math.asin(1/math.sqrt(256))
xs=[3,6,9,12]
exact=[math.sin((2*j+1)*theta)**2 for j in xs]
ax.plot(xs,exact,"--",label="Exact ideal Grover")
ax.axhline(1/256,linestyle=":",label="Random-key baseline")
ax.set_xlabel("Grover iterations")
ax.set_ylabel("Correct-key probability")
ax.set_xticks(xs)
ax.set_ylim(0,1.04)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT)
print("wrote",OUT)

if __name__=="__main__":
    pass
