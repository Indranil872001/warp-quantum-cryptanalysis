"""Explicit support-preservation check for the u=8 full-WARP sparse experiment."""

from warp import hex_to_nibbles
from warp_quantum_round import build_full_encryption, initialize_basis_state, apply_gate_list
from partial_key_grover import KEY_HEX, P1_HEX, candidate_key


def basis_tuple_for_candidate(c,u=8):
    k=hex_to_nibbles(candidate_key(c,u,0))
    p=hex_to_nibbles(P1_HEX)
    return tuple(initialize_basis_state(p,k))


def main():
    u=8
    inputs=[basis_tuple_for_candidate(c,u) for c in range(1<<u)]
    assert len(set(inputs))==(1<<u)
    gates,_=build_full_encryption()
    outputs=[]
    for b in inputs:
        outputs.append(tuple(apply_gate_list(list(b),gates)))
    assert len(set(outputs))==(1<<u)
    # Key register is retained, so distinct candidates remain distinguishable.
    assert len({o[128:] for o in outputs})==(1<<u)
    print(f"PASS: full 41-round circuit preserves sparse support size 2^{u}={1<<u}")

if __name__=="__main__":
    main()
