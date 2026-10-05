#!/usr/bin/env python3
"""Reference implementation of standard 16-bit Simplified AES (S-AES)."""

SBOX = [0x9,0x4,0xA,0xB,0xD,0x1,0x8,0x5,0x6,0x2,0x0,0x3,0xC,0xE,0xF,0x7]

def gf_mul(a,b):
    a &= 0xF; b &= 0xF; out = 0
    while b:
        if b & 1: out ^= a
        b >>= 1; a <<= 1
        if a & 0x10: a ^= 0x13
    return out & 0xF

def sub_nib_byte(x): return (SBOX[(x>>4)&0xF] << 4) | SBOX[x&0xF]
def rot_nib_byte(x): return ((x & 0xF) << 4) | ((x >> 4) & 0xF)
def g_word(w,rcon): return sub_nib_byte(rot_nib_byte(w)) ^ rcon

def expand_key(key):
    w0=(key>>8)&0xFF; w1=key&0xFF
    w2=w0^g_word(w1,0x80); w3=w2^w1
    w4=w2^g_word(w3,0x30); w5=w4^w3
    return ((w0<<8)|w1,(w2<<8)|w3,(w4<<8)|w5)

def split_nibbles(x): return [(x>>12)&0xF,(x>>8)&0xF,(x>>4)&0xF,x&0xF]
def join_nibbles(a): return ((a[0]&15)<<12)|((a[1]&15)<<8)|((a[2]&15)<<4)|(a[3]&15)
def sub_nibbles(x): return join_nibbles([SBOX[t] for t in split_nibbles(x)])

def shift_rows(x):
    a=split_nibbles(x)
    return join_nibbles([a[0],a[3],a[2],a[1]])

def mix_columns(x):
    a=split_nibbles(x)
    return join_nibbles([a[0]^gf_mul(4,a[1]),gf_mul(4,a[0])^a[1],a[2]^gf_mul(4,a[3]),gf_mul(4,a[2])^a[3]])

def encrypt(p,k):
    k0,k1,k2=expand_key(k)
    s=p^k0
    s=sub_nibbles(s); s=shift_rows(s); s=mix_columns(s); s^=k1
    s=sub_nibbles(s); s=shift_rows(s); s^=k2
    return s

def self_test():
    assert encrypt(0xD728,0x4AF5)==0x24EC

if __name__=="__main__":
    self_test()
    print("PASS D728 --4AF5--> 24EC")
