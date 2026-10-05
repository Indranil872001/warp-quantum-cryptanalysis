#!/usr/bin/env python3
"""Classical Toy-WARP-8 reference used by the manuscript demonstrator."""

SBOX=[0xC,0xA,0xD,0x3,0xE,0xB,0xF,0x7,0x8,0x9,0x1,0x5,0x0,0x2,0x4,0x6]
RC=[0x4,0xC,0xD,0xF,0xB,0x3,0x7,0xB]

def encrypt(p,k):
    x0=(p>>4)&0xF
    x1=p&0xF
    k0=(k>>4)&0xF
    k1=k&0xF
    for r in range(8):
        kr=k0 if r%2==0 else k1
        x1 ^= SBOX[x0] ^ kr ^ RC[r]
        if r<7:
            x0,x1=x1,x0
    return (x0<<4)|x1

def keyset(p,c):
    return [k for k in range(256) if encrypt(p,k)==c]

def exhaustive_self_test():
    assert encrypt(0x00,0xC6)==0xCE
    assert keyset(0x05,0x3F)==[0x18,0x2F,0xC6]
    assert keyset(0x00,0xCE)==[0xC6]

    # Every key must induce a permutation of the 256 plaintexts.
    for k in range(256):
        vals=[encrypt(p,k) for p in range(256)]
        assert len(set(vals))==256

    # Mean one-pair marked multiplicity over all true-key/plaintext choices.
    total=0
    for k in range(256):
        for p in range(256):
            c=encrypt(p,k)
            total += len(keyset(p,c))
    mean=total/(256*256)
    assert abs(mean-1.9283447265625)<1e-15
    return mean

if __name__=="__main__":
    mean=exhaustive_self_test()
    print("PASS: Toy-WARP-8 exhaustive classical checks")
    print("K=C6, P=00 ->",f"{encrypt(0x00,0xC6):02X}")
    print("keys for 05->3F:",[f"{k:02X}" for k in keyset(0x05,0x3F)])
    print("mean one-pair multiplicity:",mean)
