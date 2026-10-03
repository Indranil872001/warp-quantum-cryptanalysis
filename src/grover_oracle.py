"""
WARP-128 Grover phase-oracle constructions.

This module builds *logical* reversible circuits using:
    X, H, CNOT, Toffoli (CCX), CZ

Three main constructions are provided.

1) one_pair_oracle
   128-bit state + 128-bit key + 125 clean work ancillas = 381 qubits.
   Marks keys satisfying E_K(P1)=C1.

2) two_pair_wide_oracle
   Two 128-bit state registers + one 128-bit key + 253 clean work ancillas
   = 637 qubits.
   Both encryptions are retained and one 256-bit equality condition is
   phase-marked directly.  This minimizes comparator Toffolis among the
   constructions here.

3) two_pair_flag_oracle
   Two state registers + key + 2 equality flags + 126 work ancillas
   = 512 qubits.
   Equality bits are computed into flags; CZ(flag1,flag2) marks the AND.

4) two_pair_compact_oracle
   One state register + key + 1 equality flag + 126 work ancillas
   = 383 qubits.
   This recomputes the first encryption in order to uncompute the first
   equality flag.  It is width-efficient but gate-heavier.

All work/flag ancillas are returned to |0> by each phase oracle.
"""

from warp import hex_to_nibbles
from warp_quantum_round import build_full_encryption

# Official same-key WARP vectors used in the experiments.
KEY_HEX = "0123456789ABCDEFFEDCBA9876543210"
P1_HEX  = "0123456789ABCDEFFEDCBA9876543210"
C1_HEX  = "24CE0A8EFD9F32DE529D5FDF45703A8D"
P2_HEX  = "00112233445566778899AABBCCDDEEFF"
C2_HEX  = "923C64F92827EE62B9667DD2548FB12C"


def nibble_hex_to_lsb_bits(h):
    ns = hex_to_nibbles(h)
    out = []
    for n in ns:
        out.extend((n >> j) & 1 for j in range(4))
    return out


P1_BITS = nibble_hex_to_lsb_bits(P1_HEX)
C1_BITS = nibble_hex_to_lsb_bits(C1_HEX)
P2_BITS = nibble_hex_to_lsb_bits(P2_HEX)
C2_BITS = nibble_hex_to_lsb_bits(C2_HEX)


def remap_gate(g, state_base, key_base):
    """
    Phase-2B encryption uses local wires:
        0..127 state, 128..255 key.
    Remap to arbitrary state/key bases.
    """
    def m(q):
        if q < 128:
            return state_base + q
        return key_base + (q - 128)
    return (g[0],) + tuple(m(q) for q in g[1:])


def remap_encryption(state_base, key_base):
    gates, fmap = build_full_encryption()
    rg = [remap_gate(g,state_base,key_base) for g in gates]
    rfmap = [[state_base + q for q in nib] for nib in fmap]
    return rg, rfmap


def state_bits_in_logical_order(final_map):
    """Return 128 physical wires corresponding to logical bits X0..X31."""
    return [q for nib in final_map for q in nib]


def append_load_classical(gates, state_base, bits):
    for i,b in enumerate(bits):
        if b:
            gates.append(("X", state_base+i))


def append_xor_classical(gates, state_base, bits_a, bits_b):
    for i,(a,b) in enumerate(zip(bits_a,bits_b)):
        if a ^ b:
            gates.append(("X", state_base+i))


def append_normalize_to_ones(gates, logical_wires, target_bits):
    """
    For equality to a classical target, flip wires whose desired bit is 0.
    Then all wires are 1 iff the register equals the target.
    """
    for q,b in zip(logical_wires,target_bits):
        if b == 0:
            gates.append(("X",q))


def append_mcx_clean(gates, controls, target, ancillas):
    """
    Exact multi-controlled X using a clean AND ladder.

    For m controls >= 2:
      clean ancillas required = m-2
      Toffolis = 2m-3

    All ancillas are returned to zero.
    """
    m = len(controls)
    if m == 0:
        gates.append(("X",target))
        return
    if m == 1:
        gates.append(("CX",controls[0],target))
        return
    if m == 2:
        gates.append(("CCX",controls[0],controls[1],target))
        return

    need = m-2
    if len(ancillas) < need:
        raise ValueError(f"need {need} clean ancillas, got {len(ancillas)}")
    a = ancillas[:need]

    gates.append(("CCX", controls[0], controls[1], a[0]))
    # a[j-1] accumulates controls 0..j for j=2..m-2
    for j in range(2,m-1):
        gates.append(("CCX", a[j-2], controls[j], a[j-1]))

    gates.append(("CCX", a[m-3], controls[m-1], target))

    for j in range(m-2,1,-1):
        gates.append(("CCX", a[j-2], controls[j], a[j-1]))
    gates.append(("CCX", controls[0], controls[1], a[0]))


def append_mcz_clean(gates, condition_bits, ancillas):
    """
    Phase-flip iff every qubit in condition_bits is 1.

    Choose the last condition qubit as target:
        H(target) ; MCX(other controls -> target) ; H(target).

    For n condition bits >=3:
      clean ancillas = n-3
      Toffolis = 2n-5.
    Example n=128: 125 ancillas, 251 CCX.
    """
    n = len(condition_bits)
    if n == 1:
        gates.append(("Z",condition_bits[0]))
        return
    if n == 2:
        gates.append(("CZ",condition_bits[0],condition_bits[1]))
        return

    target = condition_bits[-1]
    controls = condition_bits[:-1]
    need = len(controls)-2
    if len(ancillas) < need:
        raise ValueError(f"need {need} clean ancillas, got {len(ancillas)}")
    gates.append(("H",target))
    append_mcx_clean(gates,controls,target,ancillas[:need])
    gates.append(("H",target))


def append_equality_flag(gates, logical_wires, target_bits, flag, ancillas):
    """flag ^= [register == target], preserving the register."""
    append_normalize_to_ones(gates,logical_wires,target_bits)
    append_mcx_clean(gates,logical_wires,flag,ancillas)
    append_normalize_to_ones(gates,logical_wires,target_bits)


def inverse_gate_list(gates):
    """
    All gates used here are self-inverse.
    Reversing the list gives the inverse for unitary subcircuits.
    """
    return list(reversed(gates))


def one_pair_oracle(target_bits=C1_BITS):
    # layout: state 0..127, key 128..255, work 256..380
    state_base,key_base,anc_base = 0,128,256
    anc = list(range(anc_base,anc_base+125))

    E,fmap = remap_encryption(state_base,key_base)
    wires = state_bits_in_logical_order(fmap)

    g=[]
    g.extend(E)
    append_normalize_to_ones(g,wires,target_bits)
    append_mcz_clean(g,wires,anc)
    append_normalize_to_ones(g,wires,target_bits)
    g.extend(inverse_gate_list(E))
    return g, 381


def two_pair_wide_oracle(c1=C1_BITS,c2=C2_BITS):
    """
    Direct 256-bit equality phase:
       [E_K(P1)=C1] AND [E_K(P2)=C2].

    layout:
      state1 0..127
      state2 128..255
      key    256..383
      work   384..636  (253 clean ancillas)
    """
    s1,s2,k,ab = 0,128,256,384
    anc=list(range(ab,ab+253))

    E1,fm1=remap_encryption(s1,k)
    E2,fm2=remap_encryption(s2,k)
    w1=state_bits_in_logical_order(fm1)
    w2=state_bits_in_logical_order(fm2)

    g=[]
    g.extend(E1)
    g.extend(E2)

    append_normalize_to_ones(g,w1,c1)
    append_normalize_to_ones(g,w2,c2)
    append_mcz_clean(g,w1+w2,anc)
    append_normalize_to_ones(g,w2,c2)
    append_normalize_to_ones(g,w1,c1)

    g.extend(inverse_gate_list(E2))
    g.extend(inverse_gate_list(E1))
    return g,637


def two_pair_flag_oracle(c1=C1_BITS,c2=C2_BITS):
    """
    Two-state / two-flag construction.

    layout:
      state1 0..127
      state2 128..255
      key    256..383
      flags  384,385
      work   386..511 (126 clean ancillas)
    """
    s1,s2,k=0,128,256
    f1,f2=384,385
    anc=list(range(386,512))

    E1,fm1=remap_encryption(s1,k)
    E2,fm2=remap_encryption(s2,k)
    w1=state_bits_in_logical_order(fm1)
    w2=state_bits_in_logical_order(fm2)

    g=[]
    g.extend(E1)
    g.extend(E2)

    append_equality_flag(g,w1,c1,f1,anc)
    append_equality_flag(g,w2,c2,f2,anc)
    g.append(("CZ",f1,f2))
    append_equality_flag(g,w2,c2,f2,anc)
    append_equality_flag(g,w1,c1,f1,anc)

    g.extend(inverse_gate_list(E2))
    g.extend(inverse_gate_list(E1))
    return g,512


def two_pair_compact_oracle(p1=P1_BITS,c1=C1_BITS,p2=P2_BITS,c2=C2_BITS):
    """
    Width-oriented construction using one 128-bit state register.

    layout:
      state 0..127
      key   128..255
      flag  256
      work  257..382 (126 clean ancillas)

    The first encryption is recomputed at the end to uncompute f1.
    """
    s,k,f=0,128,256
    anc=list(range(257,383))

    E,fmap=remap_encryption(s,k)
    w=state_bits_in_logical_order(fmap)

    g=[]
    # Pair 1.
    g.extend(E)
    append_equality_flag(g,w,c1,f,anc)
    g.extend(inverse_gate_list(E))       # return to P1

    # Change known plaintext P1 -> P2 in the state register.
    append_xor_classical(g,s,p1,p2)

    # Pair 2 and joint phase with f1.
    g.extend(E)
    append_normalize_to_ones(g,w,c2)
    append_mcz_clean(g,[f]+w,anc)        # condition on f1 AND equality2
    append_normalize_to_ones(g,w,c2)
    g.extend(inverse_gate_list(E))       # return to P2

    # Restore P1.
    append_xor_classical(g,s,p1,p2)

    # Recompute pair 1 solely to uncompute the stored flag.
    g.extend(E)
    append_equality_flag(g,w,c1,f,anc)
    g.extend(inverse_gate_list(E))
    return g,383


def diffuser_128(key_wires, ancillas):
    """
    Standard Grover diffuser on 128 key qubits:
      H^n X^n MCZ X^n H^n.
    """
    g=[]
    for q in key_wires:
        g.append(("H",q))
    for q in key_wires:
        g.append(("X",q))
    append_mcz_clean(g,key_wires,ancillas)
    for q in key_wires:
        g.append(("X",q))
    for q in key_wires:
        g.append(("H",q))
    return g


def one_pair_iteration():
    oracle,nq=one_pair_oracle()
    key=list(range(128,256))
    anc=list(range(256,381))
    return oracle+diffuser_128(key,anc),nq


def two_pair_wide_iteration():
    oracle,nq=two_pair_wide_oracle()
    key=list(range(256,384))
    anc=list(range(384,637))
    return oracle+diffuser_128(key,anc[:125]),nq


def two_pair_flag_iteration():
    oracle,nq=two_pair_flag_oracle()
    key=list(range(256,384))
    anc=list(range(386,512))
    return oracle+diffuser_128(key,anc[:125]),nq


def two_pair_compact_iteration():
    oracle,nq=two_pair_compact_oracle()
    key=list(range(128,256))
    anc=list(range(257,383))
    return oracle+diffuser_128(key,anc[:125]),nq
