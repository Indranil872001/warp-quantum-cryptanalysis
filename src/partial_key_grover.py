"""
Executable Grover demonstrator over a partial key space of FULL 41-round WARP.

Important:
- The cipher is NOT reduced-round and the state is NOT reduced.
- Only u master-key bits are declared unknown.
- All remaining master-key bits are fixed to their values in an official
  WARP test vector.
- The Grover statevector is simulated over 2^u key candidates.
- The oracle predicate is evaluated using the real 41-round WARP encryption.

This demonstrates amplitude amplification and key recovery without pretending
that a 256+ qubit full gate-level statevector can be simulated classically.
"""

import math
import numpy as np

from warp import encrypt_hex

KEY_HEX = "0123456789ABCDEFFEDCBA9876543210"
P1_HEX  = "0123456789ABCDEFFEDCBA9876543210"
C1_HEX  = "24CE0A8EFD9F32DE529D5FDF45703A8D"
P2_HEX  = "00112233445566778899AABBCCDDEEFF"
C2_HEX  = "923C64F92827EE62B9667DD2548FB12C"


def key_to_int(khex):
    return int(khex,16)

def int_to_key(x):
    return f"{x:032X}"

TRUE_KEY_INT = key_to_int(KEY_HEX)


def candidate_key(candidate, unknown_bits=8, bit_offset=0):
    """
    Replace unknown_bits of the official 128-bit key by candidate.

    bit_offset=0 means least-significant master-key bits.
    """
    if not (1 <= unknown_bits <= 24):
        raise ValueError("demonstrator supports 1..24 unknown bits")
    if not (0 <= bit_offset <= 128-unknown_bits):
        raise ValueError("invalid bit_offset")
    if not (0 <= candidate < (1<<unknown_bits)):
        raise ValueError("candidate out of range")

    mask = ((1<<unknown_bits)-1) << bit_offset
    v = (TRUE_KEY_INT & ~mask) | (candidate << bit_offset)
    return int_to_key(v)


def true_candidate(unknown_bits=8, bit_offset=0):
    return (TRUE_KEY_INT >> bit_offset) & ((1<<unknown_bits)-1)


def enumerate_marked(unknown_bits=8, bit_offset=0, pairs=1):
    """
    Return candidate integers satisfying one or two official known pairs.
    """
    marked=[]
    N=1<<unknown_bits
    for c in range(N):
        k=candidate_key(c,unknown_bits,bit_offset)
        if encrypt_hex(k,P1_HEX) != C1_HEX:
            continue
        if pairs >= 2 and encrypt_hex(k,P2_HEX) != C2_HEX:
            continue
        marked.append(c)
    return marked


def grover_statevector(marked, unknown_bits, iterations):
    """
    Exact key-register amplitude simulation.

    Oracle:
      amplitude[marked] *= -1
    Diffuser:
      a_i <- 2*mean(a) - a_i
    """
    N=1<<unknown_bits
    psi=np.ones(N,dtype=np.float64)/math.sqrt(N)
    idx=np.array(marked,dtype=np.int64)

    for _ in range(iterations):
        psi[idx] *= -1.0
        mean=psi.mean()
        psi = 2.0*mean - psi
    return psi


def marked_success_probability(psi, marked):
    if not marked:
        return 0.0
    return float(np.sum(np.abs(psi[np.array(marked,dtype=int)])**2))


def closed_form_success(N,M,k):
    if M==0:
        return 0.0
    theta=math.asin(math.sqrt(M/N))
    return math.sin((2*k+1)*theta)**2


def standard_optimal_iterations(N,M):
    """
    Integer near the first Grover maximum.
    """
    if M <= 0:
        raise ValueError("M must be positive")
    theta=math.asin(math.sqrt(M/N))
    x=math.pi/(4*theta)-0.5
    candidates={max(0,int(math.floor(x))), max(0,int(math.ceil(x)))}
    return max(candidates,key=lambda k: closed_form_success(N,M,k))


def sample_measurements(psi, shots=1024, seed=0):
    rng=np.random.default_rng(seed)
    p=np.abs(psi)**2
    draws=rng.choice(len(p),size=shots,p=p)
    counts=np.bincount(draws,minlength=len(p))
    return counts


def run_demo(unknown_bits=8,bit_offset=0,pairs=1,shots=1024,seed=2026):
    marked=enumerate_marked(unknown_bits,bit_offset,pairs)
    N=1<<unknown_bits
    M=len(marked)
    if M==0:
        raise RuntimeError("no marked key candidate in chosen subspace")

    kopt=standard_optimal_iterations(N,M)
    psi=grover_statevector(marked,unknown_bits,kopt)
    pnum=marked_success_probability(psi,marked)
    pth=closed_form_success(N,M,kopt)
    counts=sample_measurements(psi,shots,seed)

    return {
        "unknown_bits":unknown_bits,
        "bit_offset":bit_offset,
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
        "top_candidates":[
            (int(i),int(counts[i]))
            for i in np.argsort(counts)[::-1][:10]
        ],
    }
