"""
Exact sparse-branch simulation of the ACTUAL reversible WARP circuit
for a restricted unknown-key subspace.

Unlike partial_key_grover.py, which evaluates the predicate through the
independent classical implementation, this file evaluates candidate keys using
the complete Phase-2B NCT gate list for all 41 rounds.

Because the unknown key subspace contains only 2^u basis candidates, we can
track those basis branches exactly without allocating a 256-qubit dense
statevector.
"""

import math, json
import numpy as np

from warp import hex_to_nibbles, nibbles_to_hex, encrypt_hex
from warp_quantum_round import (
    build_full_encryption, initialize_basis_state,
    apply_gate_list, logical_state_from_bits,
)
from partial_key_grover import (
    KEY_HEX, P1_HEX, C1_HEX, P2_HEX, C2_HEX,
    candidate_key, true_candidate, grover_statevector,
    marked_success_probability, closed_form_success,
    standard_optimal_iterations, sample_measurements,
)

_FULL_GATES, _FINAL_MAP = build_full_encryption()

def quantum_gate_encrypt_hex(key_hex, plaintext_hex):
    key = hex_to_nibbles(key_hex)
    pt  = hex_to_nibbles(plaintext_hex)
    bits = initialize_basis_state(pt,key)
    out  = apply_gate_list(bits,_FULL_GATES)
    ct   = logical_state_from_bits(out,_FINAL_MAP)
    return nibbles_to_hex(ct)

def enumerate_marked_gatelevel(unknown_bits=8, bit_offset=0, pairs=1):
    marked=[]
    for c in range(1<<unknown_bits):
        k=candidate_key(c,unknown_bits,bit_offset)
        if quantum_gate_encrypt_hex(k,P1_HEX) != C1_HEX:
            continue
        if pairs >= 2 and quantum_gate_encrypt_hex(k,P2_HEX) != C2_HEX:
            continue
        marked.append(c)
    return marked

def run_gatelevel_demo(unknown_bits=8, bit_offset=0, pairs=1,
                       shots=1024, seed=2026):
    marked=enumerate_marked_gatelevel(unknown_bits,bit_offset,pairs)
    N=1<<unknown_bits
    M=len(marked)
    if M==0:
        raise RuntimeError("no marked candidate")
    kopt=standard_optimal_iterations(N,M)
    psi=grover_statevector(marked,unknown_bits,kopt)
    counts=sample_measurements(psi,shots,seed)
    pnum=marked_success_probability(psi,marked)
    pth=closed_form_success(N,M,kopt)
    return {
        "unknown_bits":unknown_bits,
        "pairs":pairs,
        "N":N,
        "M":M,
        "marked":marked,
        "true_candidate":true_candidate(unknown_bits,bit_offset),
        "optimal_iterations":kopt,
        "success_numeric":pnum,
        "success_theory":pth,
        "shots":shots,
        "marked_counts":{int(m):int(counts[m]) for m in marked},
    }

if __name__=="__main__":
    # Sanity: exact reversible gate circuit matches independent classical WARP
    assert quantum_gate_encrypt_hex(KEY_HEX,P1_HEX)==C1_HEX
    assert quantum_gate_encrypt_hex(KEY_HEX,P2_HEX)==C2_HEX
    print("PASS: reversible 41-round gate circuit matches both official pairs")
    print(json.dumps(run_gatelevel_demo(8,0,1,1024,2026),indent=2))
    print(json.dumps(run_gatelevel_demo(8,0,2,1024,2027),indent=2))
