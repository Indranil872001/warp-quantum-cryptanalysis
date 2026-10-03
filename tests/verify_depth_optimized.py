"""Correctness tests for the balanced phase tree on small basis-state systems."""

from depth_optimized_oracle import append_mcz_balanced


def apply_phase_gate(bits, phase, g):
    op=g[0]
    if op=="X": bits[g[1]] ^= 1
    elif op=="CX": bits[g[2]] ^= bits[g[1]]
    elif op=="CCX": bits[g[3]] ^= bits[g[1]] & bits[g[2]]
    elif op=="CZ":
        if bits[g[1]] and bits[g[2]]: phase *= -1
    elif op=="Z":
        if bits[g[1]]: phase *= -1
    else:
        raise ValueError(op)
    return phase


def check(n):
    controls=list(range(n))
    anc=list(range(n, n+(n-2)))
    gates=[]
    append_mcz_balanced(gates,controls,anc)
    for x in range(1<<n):
        bits=[(x>>j)&1 for j in range(n)] + [0]*(n-2)
        initial=list(bits)
        phase=1
        for g in gates:
            phase=apply_phase_gate(bits,phase,g)
        expected=-1 if x==(1<<n)-1 else 1
        assert phase==expected,(n,x,phase,expected)
        assert bits==initial,(n,x,bits,initial)
    return len(gates)

if __name__=="__main__":
    for n in (3,4,5,8):
        ng=check(n)
        print(f"PASS: balanced MCZ n={n}, gates={ng}")
