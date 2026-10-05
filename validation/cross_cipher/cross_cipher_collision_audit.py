#!/usr/bin/env python3
"""Cross-cipher Mini-AES / S-AES collision and two-pair uniqueness audit."""

from collections import Counter
from pathlib import Path
import csv, json, math
import numpy as np
from saes_reference import encrypt as saes_encrypt, self_test as saes_self_test

M_SBOX=[0xE,0x4,0xD,0x1,0x2,0xF,0xB,0x8,0x3,0xA,0x6,0xC,0x5,0x9,0x0,0x7]

def gf_mul(a,b):
    out=0
    while b:
        if b&1: out ^= a
        b >>= 1; a <<= 1
        if a&0x10: a ^= 0x13
    return out&0xf

def sn(x): return [(x>>12)&15,(x>>8)&15,(x>>4)&15,x&15]
def jn(a): return (a[0]<<12)|(a[1]<<8)|(a[2]<<4)|a[3]

def mini_keys(k):
    w0,w1,w2,w3=sn(k)
    w4=w0^M_SBOX[w3]^1
    w5=w1^w4; w6=w2^w5; w7=w3^w6
    w8=w4^M_SBOX[w7]^2
    w9=w5^w8; w10=w6^w9; w11=w7^w10
    return jn([w0,w1,w2,w3]),jn([w4,w5,w6,w7]),jn([w8,w9,w10,w11])

def mini_sub(x): return jn([M_SBOX[t] for t in sn(x)])
def mini_shift(x):
    a=sn(x)
    return jn([a[0],a[3],a[2],a[1]])

def mini_mix(x):
    a=sn(x)
    return jn([
        gf_mul(3,a[0])^gf_mul(2,a[1]),
        gf_mul(2,a[0])^gf_mul(3,a[1]),
        gf_mul(3,a[2])^gf_mul(2,a[3]),
        gf_mul(2,a[2])^gf_mul(3,a[3])
    ])

def mini_encrypt(p,k):
    k0,k1,k2=mini_keys(k)
    s=p^k0
    s=mini_sub(s); s=mini_shift(s); s=mini_mix(s); s^=k1
    s=mini_sub(s); s=mini_shift(s)
    return s^k2

N=1<<16
SEED=20261005
MC_TRIALS=20000
PLAINTEXTS=[
    0x0000,0xFFFF,0x1234,0xABCD,
    0x9C63,0xD728,0x0B5D,0xE0F7,
    0x1111,0x2222,0x5555,0xAAAA,
    0x1357,0x2468,0xBEEF,0xCAFE
]

def expected_occ(m):
    q=1/N
    lp=(math.lgamma(N+1)-math.lgamma(m+1)-math.lgamma(N-m+1)
        +m*math.log(q)+(N-m)*math.log1p(-q))
    return N*math.exp(lp)

EXP=[expected_occ(m) for m in range(6)]
EXP.append(N-sum(EXP))

def occ_spectrum(enc,p):
    vals=[enc(p,k) for k in range(N)]
    cc=Counter(vals)
    occ=Counter(cc.values())
    occ[0]=N-len(cc)
    obs=[occ.get(m,0) for m in range(6)]
    obs.append(sum(v for m,v in occ.items() if m>=6))
    return obs,max(occ)

def stat(obs):
    return sum((o-e)**2/e for o,e in zip(obs,EXP))

def null_stats():
    rng=np.random.default_rng(SEED)
    a=np.empty(MC_TRIALS)
    for t in range(MC_TRIALS):
        vals=rng.integers(0,N,size=N,dtype=np.int32)
        cnt=np.bincount(vals,minlength=N)
        h=np.bincount(cnt)
        obs=[int(h[m]) if m<len(h) else 0 for m in range(6)]
        obs.append(int(h[6:].sum()) if len(h)>6 else 0)
        a[t]=stat(obs)
    return a

def keyset(enc,p,c):
    return {k for k in range(N) if enc(p,k)==c}

def main():
    out=Path(__file__).resolve().parent
    saes_self_test()
    assert mini_encrypt(0x9C63,0xC3F0)==0x72C6

    null=null_stats()
    rows=[]
    for cname,enc in [("Mini-AES",mini_encrypt),("S-AES",saes_encrypt)]:
        for p in PLAINTEXTS:
            obs,mx=occ_spectrum(enc,p)
            st=stat(obs)
            pe=(1+int(np.sum(null>=st)))/(MC_TRIALS+1)
            rows.append({
                "cipher":cname,"plaintext":f"{p:04X}",
                "occ0":obs[0],"occ1":obs[1],"occ2":obs[2],
                "occ3":obs[3],"occ4":obs[4],"occ5":obs[5],
                "occ6plus":obs[6],"max_multiplicity":mx,
                "occupancy_stat":st,"mc_p_upper":pe
            })

    with open(out/"cross_cipher_occupancy.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

    studies=[]
    for cname,enc,k,p1,p2 in [
        ("Mini-AES",mini_encrypt,0xC3F0,0x9C63,0x0000),
        ("S-AES",saes_encrypt,0x4AF5,0xD728,0x0000),
    ]:
        c1=enc(p1,k); c2=enc(p2,k)
        s1=keyset(enc,p1,c1); s2=keyset(enc,p2,c2); inter=s1&s2
        studies.append({
          "cipher":cname,"true_key":f"{k:04X}",
          "P1":f"{p1:04X}","C1":f"{c1:04X}","M1":len(s1),
          "keys1":" ".join(f"{x:04X}" for x in sorted(s1)),
          "P2":f"{p2:04X}","C2":f"{c2:04X}","M2":len(s2),
          "keys2":" ".join(f"{x:04X}" for x in sorted(s2)),
          "intersection_size":len(inter),
          "intersection_keys":" ".join(f"{x:04X}" for x in sorted(inter)),
        })

    with open(out/"two_pair_uniqueness.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=studies[0].keys())
        w.writeheader(); w.writerows(studies)

    summary={}
    for cname in ("Mini-AES","S-AES"):
        subset=[r for r in rows if r["cipher"]==cname]
        summary[cname]={
          "min_mc_p":min(r["mc_p_upper"] for r in subset),
          "median_mc_p":float(np.median([r["mc_p_upper"] for r in subset])),
          "num_p_below_0.05":sum(r["mc_p_upper"]<0.05 for r in subset),
          "num_p_below_0.01":sum(r["mc_p_upper"]<0.01 for r in subset),
          "max_observed_multiplicity":max(r["max_multiplicity"] for r in subset)
        }

    pr=1/N
    pr2=1/(N*(N-1))
    summary["ideal_baseline"]={
      "mu_false_r1":(N-1)*pr,
      "p_unique_r1":(1-pr)**(N-1),
      "mu_false_r2":(N-1)*pr2,
      "p_unique_r2":(1-pr2)**(N-1)
    }
    summary["monte_carlo"]={"trials":MC_TRIALS,"seed":SEED}
    (out/"cross_cipher_summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps({"two_pair":studies,"summary":summary},indent=2))

if __name__=="__main__":
    main()
