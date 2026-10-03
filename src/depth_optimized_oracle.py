"""Depth-oriented Grover oracle variants for WARP-128.

This module adds two constructions to the baseline ladder comparators:

1. balanced 256-bit equality tree (shared quantum key), and
2. balanced equality tree plus a coherent key-copy register so the two
   WARP encryptions can be scheduled in parallel.

The balanced phase construction computes pairwise ANDs into clean ancillas
until two root bits remain, applies CZ to the two roots, and uncomputes the
AND tree. For n=2^m condition bits it uses n-2 clean ancillas, 2(n-2)
Toffoli gates and Toffoli-depth 2(m-1), versus the linear ladder's n-3
ancillas, 2n-5 Toffolis and linear Toffoli-depth.

All ancillas and the coherent key-copy register are returned to |0>.
"""

from grover_oracle import (
    C1_BITS, C2_BITS,
    remap_encryption, state_bits_in_logical_order,
    append_normalize_to_ones, inverse_gate_list,
)


def _tree_compute(gates, leaves, ancillas):
    """Compute a balanced AND tree until two roots remain.

    Returns (roots, used_ancillas, compute_gates).
    Each internal node except the final root is stored in one clean ancilla.
    We intentionally stop at two roots and use CZ for phase marking.
    """
    current = list(leaves)
    pos = 0
    compute = []
    while len(current) > 2:
        nxt = []
        # condition lengths in this project are powers of two, but support odd.
        i = 0
        while i + 1 < len(current):
            if pos >= len(ancillas):
                raise ValueError("insufficient clean ancillas for balanced tree")
            t = ancillas[pos]
            pos += 1
            g = ("CCX", current[i], current[i+1], t)
            gates.append(g)
            compute.append(g)
            nxt.append(t)
            i += 2
        if i < len(current):
            nxt.append(current[i])
        current = nxt
    return current, pos, compute


def append_mcz_balanced(gates, condition_bits, ancillas):
    """Phase flip iff all condition bits are one using a balanced AND tree.

    n=128 -> 126 ancillas, 252 CCX, 1 CZ, CCX-depth 12.
    n=256 -> 254 ancillas, 508 CCX, 1 CZ, CCX-depth 14.
    """
    n = len(condition_bits)
    if n == 0:
        raise ValueError("empty condition")
    if n == 1:
        gates.append(("Z", condition_bits[0]))
        return 0
    if n == 2:
        gates.append(("CZ", condition_bits[0], condition_bits[1]))
        return 0
    need = n - 2
    if len(ancillas) < need:
        raise ValueError(f"need {need} ancillas, got {len(ancillas)}")
    roots, used, compute = _tree_compute(gates, condition_bits, ancillas[:need])
    assert len(roots) == 2 and used == need
    gates.append(("CZ", roots[0], roots[1]))
    gates.extend(reversed(compute))
    return used


def diffuser_128_balanced(key_wires, ancillas):
    g = []
    for q in key_wires:
        g.append(("H", q))
    for q in key_wires:
        g.append(("X", q))
    append_mcz_balanced(g, key_wires, ancillas)
    for q in key_wires:
        g.append(("X", q))
    for q in key_wires:
        g.append(("H", q))
    return g


def two_pair_wide_balanced_oracle(c1=C1_BITS, c2=C2_BITS):
    """Two states share one quantum key; 256-bit balanced equality tree.

    Layout:
      state1: 0..127
      state2: 128..255
      key:    256..383
      work:   384..637 (254 clean ancillas)
    Total: 638 qubits.
    """
    s1, s2, k, ab = 0, 128, 256, 384
    anc = list(range(ab, ab + 254))
    E1, fm1 = remap_encryption(s1, k)
    E2, fm2 = remap_encryption(s2, k)
    w1 = state_bits_in_logical_order(fm1)
    w2 = state_bits_in_logical_order(fm2)

    g = []
    g.extend(E1)
    g.extend(E2)
    append_normalize_to_ones(g, w1, c1)
    append_normalize_to_ones(g, w2, c2)
    append_mcz_balanced(g, w1 + w2, anc)
    append_normalize_to_ones(g, w2, c2)
    append_normalize_to_ones(g, w1, c1)
    g.extend(inverse_gate_list(E2))
    g.extend(inverse_gate_list(E1))
    return g, 638


def two_pair_wide_balanced_iteration():
    oracle, nq = two_pair_wide_balanced_oracle()
    key = list(range(256, 384))
    anc = list(range(384, 638))
    return oracle + diffuser_128_balanced(key, anc[:126]), nq


def two_pair_parallel_balanced_oracle(c1=C1_BITS, c2=C2_BITS):
    """Depth-oriented two-pair oracle with coherent key fanout.

    A second 128-qubit key register is initialized to |0> and coherently
    populated by CNOTs from the primary key.  This is not cloning an arbitrary
    state: it creates the standard computational-basis fanout/cat correlation
    needed to use the key bits as controls in a disjoint second encryption.
    After both encryption circuits are uncomputed, the copy is erased by the
    inverse CNOT fanout.

    Layout:
      state1:  0..127
      state2: 128..255
      key:    256..383
      keycopy:384..511
      work:   512..765 (254 comparator ancillas)
    Total: 766 qubits.
    """
    s1, s2, k, kc, ab = 0, 128, 256, 384, 512
    anc = list(range(ab, ab + 254))

    E1, fm1 = remap_encryption(s1, k)
    E2, fm2 = remap_encryption(s2, kc)
    w1 = state_bits_in_logical_order(fm1)
    w2 = state_bits_in_logical_order(fm2)

    fanout = [("CX", k + i, kc + i) for i in range(128)]

    g = []
    g.extend(fanout)
    # These lists are appended sequentially, but dependency-aware scheduling
    # can place E1 and E2 in parallel because their state/key wires are disjoint.
    g.extend(E1)
    g.extend(E2)
    append_normalize_to_ones(g, w1, c1)
    append_normalize_to_ones(g, w2, c2)
    append_mcz_balanced(g, w1 + w2, anc)
    append_normalize_to_ones(g, w2, c2)
    append_normalize_to_ones(g, w1, c1)
    g.extend(inverse_gate_list(E2))
    g.extend(inverse_gate_list(E1))
    g.extend(reversed(fanout))
    return g, 766


def two_pair_parallel_balanced_iteration():
    oracle, nq = two_pair_parallel_balanced_oracle()
    key = list(range(256, 384))
    anc = list(range(512, 766))
    return oracle + diffuser_128_balanced(key, anc[:126]), nq
