"""
Small, dependency-light stochastic Pauli noise helpers.

Noise convention
----------------
After each ideal gate, with probability p_g, apply a uniformly random
non-identity Pauli error to the qubits touched by that gate.

For a k-qubit gate this is the standard k-qubit depolarizing Pauli mixture:
each non-identity Pauli string in the k-fold Pauli set, excluding the all-identity string
is chosen with equal probability.

This is an idealized *logical gate* noise model.  It is not claimed to
represent any specific IBM/Quantinuum/IonQ device.
"""

import random

PAULIS = (0,1,2,3)  # I,X,Y,Z

def apply_classical_gate(bits,g):
    op=g[0]
    if op=="X":
        bits[g[1]] ^= 1
    elif op=="CX":
        bits[g[2]] ^= bits[g[1]]
    elif op=="CCX":
        bits[g[3]] ^= bits[g[1]] & bits[g[2]]
    else:
        raise ValueError(op)

def touched(g):
    return list(g[1:])

def sample_nonidentity_pauli(k,rng):
    """Return tuple in {I,X,Y,Z}^k excluding all-I."""
    while True:
        p=tuple(rng.randrange(4) for _ in range(k))
        if any(x!=0 for x in p):
            return p

def apply_pauli_to_computational_bits(bits,qs,ps):
    """
    On a computational basis state, X and Y flip the observed bit; Z does not.
    This is sufficient for S-box truth-table success measurements because no
    superposition is present in the NCT circuit.
    """
    for q,p in zip(qs,ps):
        if p in (1,2):  # X or Y
            bits[q] ^= 1

def noisy_classical_trajectory(bits,gates,p1,p2,p3,rng):
    bits=list(bits)
    for g in gates:
        apply_classical_gate(bits,g)
        qs=touched(g)
        p={1:p1,2:p2,3:p3}[len(qs)]
        if rng.random() < p:
            ps=sample_nonidentity_pauli(len(qs),rng)
            apply_pauli_to_computational_bits(bits,qs,ps)
    return bits
