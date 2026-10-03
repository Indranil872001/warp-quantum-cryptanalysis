"""
Qiskit 2.x / Aer local verification for the WARP small components.

IBM credentials are not used.

Requires:
  qiskit ~= 2.5
  qiskit-aer == 0.17.2
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from midori_sbox import SBOX, INPLACE_GATES, OUT_WIRE_FOR_Y, sxor_optimized_gate_list

def emit(qc,g):
    if g[0]=="X": qc.x(g[1])
    elif g[0]=="CX": qc.cx(g[1],g[2])
    elif g[0]=="CCX": qc.ccx(g[1],g[2],g[3])
    else: raise ValueError(g)

def load_basis(qc,value,n,offset=0):
    for j in range(n):
        if (value>>j)&1:
            qc.x(offset+j)

def run_counts(qc,shots=256):
    sim=AerSimulator()
    tqc=transpile(qc,sim,optimization_level=0)
    return sim.run(tqc,shots=shots).result().get_counts()

def verify_sbox():
    for x in range(16):
        qc=QuantumCircuit(4,4)
        load_basis(qc,x,4)
        for g in INPLACE_GATES: emit(qc,g)
        # logical y_j lives on physical OUT_WIRE_FOR_Y[j]
        for j in range(4):
            qc.measure(OUT_WIRE_FOR_Y[j],j)
        counts=run_counts(qc,128)
        got=max(counts,key=counts.get)
        # Qiskit count string is c3...c0
        val=int(got,2)
        assert val==SBOX[x],(x,val,SBOX[x])
    print("PASS: Qiskit/Aer Sb0 truth table")

def verify_sxor():
    gates=sxor_optimized_gate_list()
    for x in range(16):
        for y in range(16):
            qc=QuantumCircuit(8,8)
            load_basis(qc,x,4,0)
            load_basis(qc,y,4,4)
            for g in gates: emit(qc,g)
            qc.measure(range(8),range(8))
            counts=run_counts(qc,64)
            got=int(max(counts,key=counts.get),2)
            xo=got & 0xF
            yo=(got>>4)&0xF
            assert xo==x and yo==(y^SBOX[x]),(x,y,xo,yo)
    print("PASS: Qiskit/Aer clean S-XOR truth table")

if __name__=="__main__":
    verify_sbox()
    verify_sxor()
