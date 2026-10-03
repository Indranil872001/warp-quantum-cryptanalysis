"""
Reference-style Python implementation of WARP-128.

Specification:
Subhadeep Banik et al., "WARP: Revisiting GFN for Lightweight
128-bit Block Cipher", SAC 2020 / IACR ePrint 2020/1320.

State convention:
- 128-bit block = 32 hexadecimal nibbles X[0]..X[31], in the order
  printed in the WARP specification.
- 128-bit key = 32 hexadecimal nibbles. K0=first 16 nibbles,
  K1=last 16 nibbles.
"""

SBOX = [
    0xC, 0xA, 0xD, 0x3,
    0xE, 0xB, 0xF, 0x7,
    0x8, 0x9, 0x1, 0x5,
    0x0, 0x2, 0x4, 0x6,
]

PERM = [
    31, 6, 29, 14, 1, 12, 21, 8,
    27, 2, 3, 0, 25, 4, 23, 10,
    15, 22, 13, 30, 17, 28, 5, 24,
    11, 18, 19, 16, 9, 20, 7, 26,
]

INV_PERM = [0] * 32
for _i, _p in enumerate(PERM):
    INV_PERM[_p] = _i


def generate_round_constants():
    """
    Generate the 41 pairs (RC0, RC1) from the 6-bit LFSR in the specification.

    LFSR state is (l5,l4,l3,l2,l1,l0), initialized to 000001.
    Update:
      (l5,l4,l3,l2,l1,l0) <- (l4,l3,l2,l1,l0,l0 xor l5)
    RC0 = (l5,l4,l3,l2), RC1 = (l1,l0,0,0).
    """
    state = [0, 0, 0, 0, 0, 1]
    out = []
    for _ in range(41):
        l5, l4, l3, l2, l1, l0 = state
        rc0 = (l5 << 3) | (l4 << 2) | (l3 << 1) | l2
        rc1 = (l1 << 3) | (l0 << 2)
        out.append((rc0, rc1))
        state = [l4, l3, l2, l1, l0, l0 ^ l5]
    return out


ROUND_CONSTANTS = generate_round_constants()


def hex_to_nibbles(x):
    x = x.strip().replace("0x", "").replace(" ", "").replace("_", "")
    if len(x) != 32:
        raise ValueError("WARP input must contain exactly 32 hex nibbles (128 bits).")
    try:
        return [int(c, 16) for c in x]
    except ValueError as exc:
        raise ValueError("Input contains a non-hexadecimal character.") from exc


def nibbles_to_hex(x):
    if len(x) != 32 or any(not (0 <= v < 16) for v in x):
        raise ValueError("Expected 32 nibbles.")
    return "".join(f"{v:X}" for v in x)


def _key_halves(key):
    if len(key) != 32:
        raise ValueError("Key must contain 32 nibbles.")
    return key[:16], key[16:]


def _feistel_layer(state, round_key):
    """In-place WARP nonlinear/key layer before the shuffle."""
    for i in range(16):
        state[2 * i + 1] ^= SBOX[state[2 * i]] ^ round_key[i]


def _add_round_constant(state, r):
    """r is zero-based: 0..40."""
    rc0, rc1 = ROUND_CONSTANTS[r]
    state[1] ^= rc0
    state[3] ^= rc1


def _shuffle(state):
    out = [0] * 32
    # Specification: X_{pi[j]} <- X'_j
    for j in range(32):
        out[PERM[j]] = state[j]
    return out


def _inverse_shuffle(state):
    out = [0] * 32
    for j in range(32):
        out[INV_PERM[j]] = state[j]
    return out


def encrypt_nibbles(key, plaintext):
    """
    Encrypt one 128-bit block represented as 32 nibbles.
    Returns 32 ciphertext nibbles.
    """
    k0, k1 = _key_halves(list(key))
    x = list(plaintext)

    # Rounds 1..40: nonlinear/key layer + constants + shuffle.
    for r in range(40):
        rk = k0 if (r % 2 == 0) else k1
        _feistel_layer(x, rk)
        _add_round_constant(x, r)
        x = _shuffle(x)

    # Round 41: K0, no final shuffle.
    _feistel_layer(x, k0)
    _add_round_constant(x, 40)
    return x


def decrypt_nibbles(key, ciphertext):
    """
    Decrypt one 128-bit block represented as 32 nibbles.
    """
    k0, k1 = _key_halves(list(key))
    x = list(ciphertext)

    # Undo round 41. The Feistel/XOR layer is self-inverse when the
    # even branch is held fixed; constants are XORs as well.
    _add_round_constant(x, 40)
    _feistel_layer(x, k0)

    # Undo rounds 40..1.
    for r in range(39, -1, -1):
        x = _inverse_shuffle(x)
        _add_round_constant(x, r)
        rk = k0 if (r % 2 == 0) else k1
        _feistel_layer(x, rk)

    return x


def encrypt_hex(key_hex, plaintext_hex):
    return nibbles_to_hex(
        encrypt_nibbles(hex_to_nibbles(key_hex), hex_to_nibbles(plaintext_hex))
    )


def decrypt_hex(key_hex, ciphertext_hex):
    return nibbles_to_hex(
        decrypt_nibbles(hex_to_nibbles(key_hex), hex_to_nibbles(ciphertext_hex))
    )


if __name__ == "__main__":
    # First official test vector.
    K = "0123456789ABCDEFFEDCBA9876543210"
    P = "0123456789ABCDEFFEDCBA9876543210"
    C = encrypt_hex(K, P)
    print("K =", K)
    print("P =", P)
    print("C =", C)
