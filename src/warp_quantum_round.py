"""
Verified reversible WARP round and full-encryption circuit generator.

Register convention
-------------------
State qubits:
    q[0]..q[127]
    logical nibble X_i initially occupies q[4*i + j], j=0..3 (LSB first).

Quantum key qubits:
    q[128]..q[255]
    master-key nibble K_i occupies q[128 + 4*i + j].

WARP has no expanded-key register.  K0 (nibbles 0..15) and K1
(nibbles 16..31) are selected alternately.

The 32-nibble WARP shuffle is implemented as a *virtual wire relabeling*.
Therefore it contributes zero logical gates.  This is exact for a logical
circuit model; a separate optional SWAP realization is provided for routing
studies.

Gate tuples:
    ("X", target)
    ("CX", control, target)
    ("CCX", control1, control2, target)

All three gate types are self-inverse.
"""

from collections import Counter
from warp import PERM, ROUND_CONSTANTS
from midori_sbox import INPLACE_GATES, OUT_WIRE_FOR_Y

N_STATE = 128
N_KEY = 128
N_QUBITS = 256


def initial_state_map():
    """Logical nibble/bit -> physical state qubit."""
    return [[4*i + j for j in range(4)] for i in range(32)]


def key_map():
    """Master-key nibble/bit -> physical key qubit."""
    return [[N_STATE + 4*i + j for j in range(4)] for i in range(32)]


def map_local_gate(g, wires):
    op = g[0]
    if op == "X":
        return ("X", wires[g[1]])
    if op == "CX":
        return ("CX", wires[g[1]], wires[g[2]])
    if op == "CCX":
        return ("CCX", wires[g[1]], wires[g[2]], wires[g[3]])
    raise ValueError(op)


def append_sxor(gates, xw, yw):
    """
    Append clean WARP Feistel nonlinear primitive
        |x>|y> -> |x>|y xor S(x)>
    using the Phase-2A compute-copy-uncompute construction.
    """
    gates.extend(map_local_gate(g, xw) for g in INPLACE_GATES)

    # Logical S-box output y_j sits on physical S-box wire OUT_WIRE_FOR_Y[j].
    for j in range(4):
        gates.append(("CX", xw[OUT_WIRE_FOR_Y[j]], yw[j]))

    gates.extend(map_local_gate(g, xw) for g in reversed(INPLACE_GATES))


def add_round_key(gates, y_wires, key_wires):
    for j in range(4):
        gates.append(("CX", key_wires[j], y_wires[j]))


def add_round_constant(gates, state_map, r):
    """
    WARP adds RC0 to logical nibble X_1 and RC1 to logical nibble X_3.
    Constants are classical, hence X gates only.
    """
    rc0, rc1 = ROUND_CONSTANTS[r]
    for j in range(4):
        if (rc0 >> j) & 1:
            gates.append(("X", state_map[1][j]))
        if (rc1 >> j) & 1:
            gates.append(("X", state_map[3][j]))


def virtual_shuffle(state_map):
    """
    Specification convention:
        X_{PERM[j]} <- X'_j.
    No quantum gate is emitted; only the logical-to-physical map changes.
    """
    out = [None] * 32
    for j in range(32):
        out[PERM[j]] = list(state_map[j])
    return out


def build_round(r, state_map=None):
    """
    Build zero-based WARP round r in {0,...,40}.

    Rounds 0..39 include the nibble shuffle.
    Round 40 is the final round and omits it.

    Returns:
        gates, new_state_map
    """
    if not (0 <= r <= 40):
        raise ValueError("round index must be 0..40")

    if state_map is None:
        state_map = initial_state_map()
    state_map = [list(w) for w in state_map]
    km = key_map()

    # r even => K0, r odd => K1.
    half = r & 1
    gates = []

    for i in range(16):
        xw = state_map[2*i]
        yw = state_map[2*i + 1]
        append_sxor(gates, xw, yw)

        kw = km[16*half + i]
        add_round_key(gates, yw, kw)

    add_round_constant(gates, state_map, r)

    new_map = virtual_shuffle(state_map) if r < 40 else state_map
    return gates, new_map


def build_full_encryption():
    """
    Return the complete 41-round logical WARP encryption circuit:
        gates, final_state_map

    Qubit width = 128 state + 128 quantum key = 256.
    No ancilla qubits are used by this baseline.
    """
    smap = initial_state_map()
    gates = []
    for r in range(41):
        rg, smap = build_round(r, smap)
        gates.extend(rg)
    return gates, smap


def inverse_gate_list(gates):
    """All gates in this NCT circuit are self-inverse."""
    return list(reversed(gates))


def apply_gate(bits, gate):
    op = gate[0]
    if op == "X":
        bits[gate[1]] ^= 1
    elif op == "CX":
        c,t = gate[1:]
        bits[t] ^= bits[c]
    elif op == "CCX":
        a,b,t = gate[1:]
        bits[t] ^= bits[a] & bits[b]
    else:
        raise ValueError(op)


def apply_gate_list(bits, gates):
    bits = list(bits)
    for g in gates:
        apply_gate(bits, g)
    return bits


def nibbles_to_bits(nibbles):
    out = []
    for n in nibbles:
        if not (0 <= n < 16):
            raise ValueError("not a nibble")
        out.extend((n >> j) & 1 for j in range(4))
    return out


def logical_state_from_bits(bits, state_map):
    out = []
    for wires in state_map:
        n = sum((bits[w] & 1) << j for j,w in enumerate(wires))
        out.append(n)
    return out


def initialize_basis_state(state_nibbles, key_nibbles):
    if len(state_nibbles) != 32 or len(key_nibbles) != 32:
        raise ValueError("WARP needs 32 state and 32 key nibbles")
    return nibbles_to_bits(state_nibbles) + nibbles_to_bits(key_nibbles)


def simulate_round(r, state_nibbles, key_nibbles, state_map=None, physical_bits=None):
    """
    Computational-basis simulator helper.

    For a standalone round, omit state_map/physical_bits.
    For chained rounds, pass the current physical bits and state_map.
    """
    if state_map is None:
        state_map = initial_state_map()
    if physical_bits is None:
        physical_bits = initialize_basis_state(state_nibbles, key_nibbles)

    gates, new_map = build_round(r, state_map)
    out_bits = apply_gate_list(physical_bits, gates)
    return logical_state_from_bits(out_bits, new_map), out_bits, new_map


def simulate_full_encryption(state_nibbles, key_nibbles):
    bits = initialize_basis_state(state_nibbles, key_nibbles)
    gates, final_map = build_full_encryption()
    out = apply_gate_list(bits, gates)
    return logical_state_from_bits(out, final_map), out, final_map


def gate_counts(gates):
    return Counter(g[0] for g in gates)
