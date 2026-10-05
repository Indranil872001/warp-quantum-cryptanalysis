#!/usr/bin/env python3
import math, random
from collections import Counter

SBOX=[0xC,0xA,0xD,0x3,0xE,0xB,0xF,0x7,0x8,0x9,0x1,0x5,0x0,0x2,0x4,0x6]
PERM=[31,6,29,14,1,12,21,8,27,2,3,0,25,4,23,10,15,22,13,30,17,28,5,24,11,18,19,16,9,20,7,26]
st=[0,0,0,0,0,1]; RCS=[]
for _ in range(41):
    l5,l4,l3,l2,l1,l0=st
    RCS.append(((l5<<3)|(l4<<2)|(l3<<1)|l2,(l1<<3)|(l0<<2)))
    st=[l4,l3,l2,l1,l0,l0^l5]

def h2n(s): return [int(c,16) for c in s]
def n2h(a): return ''.join(format(x,'X') for x in a)

def classical_round(x,k,r):
    x=list(x); k=list(k); rk=k[:16] if r%2==0 else k[16:]
    for i in range(16):
        x[2*i+1]^=SBOX[x[2*i]]^rk[i]
    rc0,rc1=RCS[r]; x[1]^=rc0; x[3]^=rc1
    if r<40:
        y=[0]*32
        for j in range(32): y[PERM[j]]=x[j]
        x=y
    return x

def encrypt(k,p):
    k=h2n(k) if isinstance(k,str) else list(k)
    x=h2n(p) if isinstance(p,str) else list(p)
    for r in range(41): x=classical_round(x,k,r)
    return x

SBOX_GATES=[
("CX",0,2),("CCX",0,2,3),("CCX",2,3,0),("X",3),
("CX",1,3),("CX",0,2),("CCX",0,3,1),("CCX",1,3,0),
("CX",1,3),("X",0)]
OUT=[1,2,3,0]

def qmap(base=0): return [[base+4*i+j for j in range(4)] for i in range(32)]
def mapped(g,w): return tuple([g[0]]+[w[z] for z in g[1:]])
def sxor(gs,xw,yw):
    gs += [mapped(g,xw) for g in SBOX_GATES]
    for j in range(4): gs.append(("CX",xw[OUT[j]],yw[j]))
    gs += [mapped(g,xw) for g in reversed(SBOX_GATES)]
def shuffle(sm):
    y=[None]*32
    for j in range(32): y[PERM[j]]=sm[j][:]
    return y

def build_encryption():
    sm=qmap(0); km=qmap(128); gs=[]
    for r in range(41):
        half=r&1
        for i in range(16):
            sxor(gs,sm[2*i],sm[2*i+1])
            kw=km[16*half+i]
            for j in range(4): gs.append(("CX",kw[j],sm[2*i+1][j]))
        rc0,rc1=RCS[r]
        for j in range(4):
            if (rc0>>j)&1: gs.append(("X",sm[1][j]))
            if (rc1>>j)&1: gs.append(("X",sm[3][j]))
        if r<40: sm=shuffle(sm)
    return gs,sm
GATES,FINAL_MAP=build_encryption()

def bits(p,k):
    out=[]
    for n in list(p)+list(k): out += [(n>>j)&1 for j in range(4)]
    return out
def run(gs,b):
    b=b[:]
    for g in gs:
        if g[0]=="X": b[g[1]]^=1
        elif g[0]=="CX": b[g[2]]^=b[g[1]]
        else: b[g[3]] ^= b[g[1]]&b[g[2]]
    return b
def read_state(b,sm):
    return [sum(b[w[j]]<<j for j in range(4)) for w in sm]

cnt=Counter(g[0] for g in GATES)
assert cnt==Counter({"X":2763,"CX":10496,"CCX":5248})
assert len(GATES)==18507
assert sum(a.bit_count()+b.bit_count() for a,b in RCS)==139

VECTORS=[
("0123456789ABCDEFFEDCBA9876543210","0123456789ABCDEFFEDCBA9876543210","24CE0A8EFD9F32DE529D5FDF45703A8D"),
("0123456789ABCDEFFEDCBA9876543210","00112233445566778899AABBCCDDEEFF","923C64F92827EE62B9667DD2548FB12C"),
("0ACD022F680A547FEE03C0867B09E3D7","AF6CDD90FC5A6EAA897BCD1208D391E1","6123995F1924D31425641ACDD058DD46")]
for k,p,c in VECTORS:
    assert n2h(encrypt(k,p))==c
    assert n2h(read_state(run(GATES,bits(h2n(p),h2n(k))),FINAL_MAP))==c

rng=random.Random(20261005)
for _ in range(100):
    k=[rng.randrange(16) for _ in range(32)]
    p=[rng.randrange(16) for _ in range(32)]
    initial=bits(p,k)
    out=run(GATES,initial)
    assert read_state(out,FINAL_MAP)==encrypt(k,p)
    assert run(list(reversed(GATES)),out)==initial

for _ in range(1000):
    k=[rng.randrange(16) for _ in range(32)]
    x=[rng.randrange(16) for _ in range(32)]
    r=rng.randrange(41)
    expected=classical_round(x,k,r)
    sm=qmap(0); km=qmap(128); gs=[]; half=r&1
    for i in range(16):
        sxor(gs,sm[2*i],sm[2*i+1])
        kw=km[16*half+i]
        for j in range(4): gs.append(("CX",kw[j],sm[2*i+1][j]))
    rc0,rc1=RCS[r]
    for j in range(4):
        if (rc0>>j)&1: gs.append(("X",sm[1][j]))
        if (rc1>>j)&1: gs.append(("X",sm[3][j]))
    final=shuffle(sm) if r<40 else sm
    assert read_state(run(gs,bits(x,k)),final)==expected

R=(math.pi/4)*2**64
Titer=152250
p0=(1-1e-5)**207560*(1-1e-4)**172484
assert abs(math.log2(R)-63.65149612947232)<1e-12
assert abs(math.log2(R*Titer)-80.86757883204073)<1e-12
assert abs(p0-4.048688418520039e-9)<1e-20

for N,j,pref in [
    (256,12,0.9999470421032736),
    (1024,25,0.9994612447444079),
    (4096,50,0.999945346109049),
]:
    th=math.asin(1/math.sqrt(N))
    pp=math.sin((2*j+1)*th)**2
    assert abs(pp-pref)<1e-12

print("PASS: WARP gate totals")
print("PASS: all 3 official WARP vectors")
print("PASS: 100 seeded random full encryptions")
print("PASS: inverse-gate restoration on all 100 random cases")
print("PASS: 1,000 seeded random standalone rounds")
print("PASS: restricted-key Grover probabilities")
print("PASS: Grover/T-work logarithms")
print("PASS: full-oracle no-fault arithmetic")
print("resource_counts",dict(cnt),"total",len(GATES))
print("round_constant_weight_sum",sum(a.bit_count()+b.bit_count() for a,b in RCS))
print("log2_grover_iterations",math.log2(R))
print("log2_total_T",math.log2(R*Titer))
print("no_fault_proxy",p0)