"""
Paper-aligned component-wise logical noise analysis for WARP.

The uploaded Mini-AES paper reports noise separately for nonlinear,
linear/permutation, and other oracle modules.  For WARP we evaluate:

1. 4-bit in-place Sb0;
2. 8-bit Feistel nonlinear map |x>|y> -> |x>|y xor S(x)>;
3. 4-bit quantum round-key addition y ^= k;
4. one complete 256-qubit logical WARP round on random basis inputs.

The nibble shuffle is virtual wire relabeling in our logical circuit and thus
has zero logical gate noise; physical routing noise is a separate hardware
mapping question.

Noise model:
after each X/CX/CCX gate, with probabilities p1/p2/p3, apply a uniformly
random non-identity Pauli string to the gate's touched qubits.  On basis-state
truth-table tests, X/Y flip observed bits and Z does not.

This is a logical sensitivity model, not a hardware calibration model.
"""

import random, math, csv
from midori_sbox import (
    SBOX, INPLACE_GATES, OUT_WIRE_FOR_Y,
    bits4, from_bits, sxor_optimized_gate_list
)
from warp_quantum_round import (
    build_round, initial_state_map, initialize_basis_state,
    logical_state_from_bits
)
from warp import _feistel_layer, _add_round_constant, _shuffle
from noise_utils import noisy_classical_trajectory

SCENARIOS = [
    ("ideal",0.0,0.0,0.0),
    ("low",1e-4,1e-4,2e-4),
    ("medium",5e-4,5e-4,1e-3),
    ("high",1e-3,1e-3,2e-3),
    ("very_high",5e-3,5e-3,1e-2),
]

def wilson(k,n,z=1.96):
    ph=k/n
    den=1+z*z/n
    ctr=(ph+z*z/(2*n))/den
    rad=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    return ctr-rad,ctr+rad

def sbox_success(trials_per_input,p1,p2,p3,rng):
    good=tot=0
    for x in range(16):
        for _ in range(trials_per_input):
            raw=noisy_classical_trajectory(bits4(x),INPLACE_GATES,p1,p2,p3,rng)
            y=from_bits([raw[OUT_WIRE_FOR_Y[j]] for j in range(4)])
            good += (y==SBOX[x]); tot+=1
    return good,tot

def sxor_success(trials_per_pair,p1,p2,p3,rng):
    gates=sxor_optimized_gate_list()
    good=tot=0
    # cycle all 256 x,y pairs; repeat small number each
    for x in range(16):
        for y in range(16):
            inp=bits4(x)+bits4(y)
            exp=x, y^SBOX[x]
            for _ in range(trials_per_pair):
                out=noisy_classical_trajectory(inp,gates,p1,p2,p3,rng)
                xo=from_bits(out[:4]); yo=from_bits(out[4:8])
                good += ((xo,yo)==exp); tot+=1
    return good,tot

def keyadd_success(trials,p2,rng):
    # four CNOT gates, wires x=0..3(key), y=4..7(target)
    gates=[("CX",j,4+j) for j in range(4)]
    good=0
    for _ in range(trials):
        k=rng.randrange(16); y=rng.randrange(16)
        inp=bits4(k)+bits4(y)
        out=noisy_classical_trajectory(inp,gates,0,p2,0,rng)
        ko=from_bits(out[:4]); yo=from_bits(out[4:])
        good += (ko==k and yo==(y^k))
    return good,trials

def classical_round(r,state,key):
    x=list(state)
    rk=key[:16] if r%2==0 else key[16:]
    _feistel_layer(x,rk)
    _add_round_constant(x,r)
    if r<40: x=_shuffle(x)
    return x

def round_success(samples,r,p1,p2,p3,rng):
    gates,newmap=build_round(r,initial_state_map())
    good=0
    for _ in range(samples):
        state=[rng.randrange(16) for _ in range(32)]
        key=[rng.randrange(16) for _ in range(32)]
        inp=initialize_basis_state(state,key)
        out=noisy_classical_trajectory(inp,gates,p1,p2,p3,rng)
        got=logical_state_from_bits(out,newmap)
        # key register must also remain correct
        key_ok=(out[128:]==inp[128:])
        good += (got==classical_round(r,state,key) and key_ok)
    return good,samples

def run(seed=20261002):
    rows=[]
    for si,(label,p1,p2,p3) in enumerate(SCENARIOS):
        rng=random.Random(seed+si)
        tests=[
            ("Sb0",)+sbox_success(1000,p1,p2,p3,rng),
            ("S-XOR",)+sxor_success(30,p1,p2,p3,rng),
            ("KeyAdd",)+keyadd_success(20000,p2,rng),
            ("Round1",)+round_success(3000,0,p1,p2,p3,rng),
        ]
        for component,good,total in tests:
            lo,hi=wilson(good,total)
            rows.append({
                "scenario":label,"component":component,
                "p1":p1,"p2":p2,"p3":p3,
                "trials":total,"success":good/total,
                "ci95_low":lo,"ci95_high":hi,
            })
    return rows

if __name__=="__main__":
    rows=run()
    with open("COMPONENT_NOISE.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    for r in rows: print(r)
