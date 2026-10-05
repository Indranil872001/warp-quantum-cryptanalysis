# Mini-AES / S-AES cross-cipher validation

This directory contains the small-domain extension used in the WARP manuscript to validate the known-pair identifiability discussion.

The experiment is **not** presented as a new attack on Mini-AES or S-AES. Its purpose is to test, in fully enumerable 16-bit domains, the distinction between a key that is merely consistent with one known plaintext/ciphertext pair and the unique master key selected by multiple pairs.

## Run

```bash
python saes_reference.py
python cross_cipher_collision_audit.py
```

The audit regenerates:

- `two_pair_uniqueness.csv`;
- `cross_cipher_occupancy.csv`;
- `cross_cipher_summary.json`.

The fixed 16-plaintext panel and Monte Carlo seed/trial count are declared in the script. The manuscript applies a conservative Bonferroni correction over all 32 pre-declared Mini-AES/S-AES occupancy tests.
