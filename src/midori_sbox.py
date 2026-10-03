"""
WARP / MIDORI Sb0 quantum-circuit study (Phase 2A).

Bit convention
--------------
x = x0 + 2*x1 + 4*x2 + 8*x3, i.e. wire 0 is the LSB.

The WARP S-box LUT is:
    C A D 3 E B F 7 8 9 1 5 0 2 4 6

The 10-gate in-place NCT circuit below was independently found by an
exhaustive meet-in-the-middle search.  The physical wires at circuit output
contain a free relabeling of the S-box output:
    wire 1 = y0
    wire 2 = y1
    wire 3 = y2
    wire 0 = y3

Thus OUT_WIRE_FOR_Y = [1,2,3,0].

The circuit has:
    2 X, 4 CNOT, 4 CCX = 10 NCT gates
and full depth 32 under the metric X=1, CNOT=1, CCX=7.

Literature comparison:
- LIGHTER-R resource point reported for MIDORI: 10 gates, full depth 33.
- Chen et al. (IACR Communications in Cryptology, 2024) report
  10 gates, full depth 31 for MIDORI under their SAT model.
"""

SBOX = [0xC,0xA,0xD,0x3,0xE,0xB,0xF,0x7,
        0x8,0x9,0x1,0x5,0x0,0x2,0x4,0x6]

# Gate tuples:
# ("X", target)
# ("CX", control, target)
# ("CCX", control1, control2, target)
INPLACE_GATES = [
    ("CX",  0, 2),
    ("CCX", 0, 2, 3),
    ("CCX", 2, 3, 0),
    ("X",   3),
    ("CX",  1, 3),
    ("CX",  0, 2),
    ("CCX", 0, 3, 1),
    ("CCX", 1, 3, 0),
    ("CX",  1, 3),
    ("X",   0),
]

OUT_WIRE_FOR_Y = [1,2,3,0]

# Coordinate ANFs. Each term is a tuple of input-variable indices.
# Empty tuple means constant 1.
ANF = {
    0: [(1,), (0,2), (0,1,2), (0,3), (0,1,3), (1,2,3)],
    1: [(0,), (2,), (0,2), (0,3), (2,3)],
    2: [(), (0,), (0,1,2), (3,), (0,3), (0,1,3), (1,2,3)],
    3: [(), (0,1), (1,3), (0,1,3), (2,3), (1,2,3)],
}

def bits4(x):
    return [(x >> i) & 1 for i in range(4)]

def from_bits(b):
    return sum((int(v)&1) << i for i,v in enumerate(b))

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

def apply_gates(bits, gates):
    bits = list(bits)
    for g in gates:
        apply_gate(bits, g)
    return bits

def inplace_raw(x):
    """Physical 4-wire output of the independently synthesized circuit."""
    return from_bits(apply_gates(bits4(x), INPLACE_GATES))

def inplace_sbox(x):
    """Logical S-box output after free output-wire relabeling."""
    w = apply_gates(bits4(x), INPLACE_GATES)
    y = [w[OUT_WIRE_FOR_Y[j]] for j in range(4)]
    return from_bits(y)

def eval_anf(x):
    xb = bits4(x)
    y = [0]*4
    for j in range(4):
        v = 0
        for term in ANF[j]:
            z = 1
            for idx in term:
                z &= xb[idx]
            v ^= z
        y[j] = v
    return from_bits(y)

def sxor_compute_copy_uncompute(x, y):
    """
    Clean 8-qubit construction for the WARP Feistel primitive:
        |x>|y> -> |x>|y xor S(x)>

    It uses:
      forward in-place S circuit,
      four CNOTs from the appropriate physical output wires into y,
      reverse S circuit to restore x.

    No ancilla qubit is required.
    """
    xb = bits4(x)
    yb = bits4(y)

    # Compute physical-wire representation of S(x).
    for g in INPLACE_GATES:
        apply_gate(xb, g)

    # Copy logical y_j = S(x)_j into the Feistel target.
    for j in range(4):
        yb[j] ^= xb[OUT_WIRE_FOR_Y[j]]

    # Uncompute x.
    for g in reversed(INPLACE_GATES):
        apply_gate(xb, g)

    return from_bits(xb), from_bits(yb)

def _xor_cubic_with_one_ancilla(w, controls, target, anc):
    """
    Toggle target by product of 3 preserved input controls, using one clean ancilla:
        anc ^= a*b
        target ^= anc*c
        anc ^= a*b
    """
    a,b,c = controls
    apply_gate(w, ("CCX", a,b,anc))
    apply_gate(w, ("CCX", anc,c,target))
    apply_gate(w, ("CCX", a,b,anc))

def sxor_anf_baseline(x, y):
    """
    Straight ANF implementation of |x>|y> -> |x>|y xor S(x)>.

    Wires:
      0..3 : x
      4..7 : y
      8    : one clean ancilla

    This is deliberately a transparent baseline rather than an optimized design.
    """
    w = bits4(x) + bits4(y) + [0]
    anc = 8

    for j in range(4):
        target = 4+j
        for term in ANF[j]:
            if len(term) == 0:
                apply_gate(w, ("X", target))
            elif len(term) == 1:
                apply_gate(w, ("CX", term[0], target))
            elif len(term) == 2:
                apply_gate(w, ("CCX", term[0], term[1], target))
            elif len(term) == 3:
                _xor_cubic_with_one_ancilla(w, term, target, anc)
            else:
                raise AssertionError("unexpected ANF degree")

    assert w[8] == 0
    return from_bits(w[:4]), from_bits(w[4:8])

def sxor_optimized_gate_list():
    """
    Return an explicit 8-wire NCT gate list for compute-copy-uncompute.

    x wires = 0..3, target/odd-nibble wires = 4..7.
    """
    out = []
    out.extend(INPLACE_GATES)
    for j in range(4):
        out.append(("CX", OUT_WIRE_FOR_Y[j], 4+j))
    out.extend(reversed(INPLACE_GATES))
    return out

def anf_baseline_gate_list():
    """Explicit 9-wire gate list corresponding to sxor_anf_baseline()."""
    gates = []
    anc = 8
    for j in range(4):
        target = 4+j
        for term in ANF[j]:
            if len(term) == 0:
                gates.append(("X", target))
            elif len(term) == 1:
                gates.append(("CX", term[0], target))
            elif len(term) == 2:
                gates.append(("CCX", term[0], term[1], target))
            elif len(term) == 3:
                a,b,c = term
                gates.extend([
                    ("CCX", a,b,anc),
                    ("CCX", anc,c,target),
                    ("CCX", a,b,anc),
                ])
    return gates
