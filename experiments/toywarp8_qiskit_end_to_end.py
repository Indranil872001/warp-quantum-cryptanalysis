#!/usr/bin/env python3
"""End-to-end Qiskit/Aer Grover circuit for Toy-WARP-8.

This is the reproducibility implementation for the manuscript's reduced
8-bit full-key demonstrator.  The 8-round encryption uses the exact WARP/MIDORI
4-bit S-box and the Toy-WARP round constants described in the paper.
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

SBOX_OUT = [1,2,3,0]
SBOX_GATES = [
    ("cx",0,2),
    ("ccx",0,2,3),
    ("ccx",2,3,0),
    ("x",3),
    ("cx",1,3),
    ("cx",0,2),
    ("ccx",0,3,1),
    ("ccx",1,3,0),
    ("cx",1,3),
    ("x",0),
]
RC=[0x4,0xC,0xD,0xF,0xB,0x3,0x7,0xB]

def apply_gate(qc,g,w):
    if g[0]=="x":
        qc.x(w[g[1]])
    elif g[0]=="cx":
        qc.cx(w[g[1]],w[g[2]])
    elif g[0]=="ccx":
        qc.ccx(w[g[1]],w[g[2]],w[g[3]])
    else:
        raise ValueError(g)

def sxor(qc,source,target):
    for g in SBOX_GATES:
        apply_gate(qc,g,source)
    for j in range(4):
        qc.cx(source[SBOX_OUT[j]],target[j])
    for g in reversed(SBOX_GATES):
        apply_gate(qc,g,source)

def build_encryption():
    """Return the 16-qubit encryption circuit and physical output-bit mapping.

    Qubits 0..7 are state bits in little-endian byte order.
    Qubits 8..15 are key bits in little-endian byte order.
    """
    qc=QuantumCircuit(16,name="ToyWARP8")

    # Logical X0 is the high nibble; X1 is the low nibble.
    low=[0,1,2,3]      # X1
    high=[4,5,6,7]     # X0
    k1=[8,9,10,11]     # low key nibble
    k0=[12,13,14,15]   # high key nibble

    for r in range(8):
        sxor(qc,high,low)
        kr=k0 if r%2==0 else k1
        for j in range(4):
            qc.cx(kr[j],low[j])
        rc=RC[r]
        for j in range(4):
            if (rc>>j)&1:
                qc.x(low[j])

        # Feistel swap is a logical wire relabeling, not a physical SWAP.
        if r<7:
            high,low=low,high

    # Logical ciphertext bits 0..3 are X1, bits 4..7 are X0.
    out_bits=low+high
    return qc,out_bits

def normalize_to_target(qc,out_bits,target):
    for i,q in enumerate(out_bits):
        if ((target>>i)&1)==0:
            qc.x(q)

def phase_mark_all_ones(qc,wires):
    target=wires[-1]
    ctrls=wires[:-1]
    qc.h(target)
    qc.mcx(ctrls,target)
    qc.h(target)

def diffuser(qc,key):
    for q in key: qc.h(q)
    for q in key: qc.x(q)
    qc.h(key[-1])
    qc.mcx(key[:-1],key[-1])
    qc.h(key[-1])
    for q in key: qc.x(q)
    for q in key: qc.h(q)

def build(iterations=12, plaintext=0x00, ciphertext=0xCE):
    enc,out_bits=build_encryption()
    qc=QuantumCircuit(16,8)

    # Prepare the known plaintext on the state register.
    for i in range(8):
        if (plaintext>>i)&1:
            qc.x(i)

    key=list(range(8,16))
    for q in key:
        qc.h(q)

    for _ in range(iterations):
        qc.compose(enc,qubits=range(16),inplace=True)
        normalize_to_target(qc,out_bits,ciphertext)
        phase_mark_all_ones(qc,out_bits)
        normalize_to_target(qc,out_bits,ciphertext)
        qc.compose(enc.inverse(),qubits=range(16),inplace=True)
        diffuser(qc,key)

    qc.measure(key,range(8))
    return qc

def main():
    qc=build(iterations=12)
    sim=AerSimulator(method="statevector")
    tqc=transpile(qc,sim,optimization_level=0,seed_transpiler=777)
    result=sim.run(tqc,shots=4096,seed_simulator=101).result()
    counts=result.get_counts()
    correct=counts.get("11000110",0)
    print("correct C6:",correct,"/ 4096")
    print("success:",correct/4096)
    print("depth:",tqc.depth())
    print("counts:",counts)

if __name__=="__main__":
    main()
