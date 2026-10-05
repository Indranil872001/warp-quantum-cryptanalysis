# Quantum Key Search on WARP-128

Reproducibility repository for the manuscript

**Quantum Key Search on WARP-128: Verified Reversible Circuits, Multi-Pair Identifiability, and Success-Normalized Grover Analysis**

Authors: **Indranil Mukherjee** and **Bimal Mandal**, Indian Institute of Technology Jodhpur.

## What is implemented

### WARP-128 core
- independent classical WARP-128 reference implementation;
- verified reversible complete 41-round WARP circuit generator;
- 10-gate WARP/MIDORI `Sb0` in-place reversible implementation;
- clean Feistel `S(x)`-XOR compute-copy-uncompute primitive;
- one-pair and multiple two-pair Grover phase-oracle constructions;
- balanced equality-tree and coherent-key-fanout depth-oriented oracle variants;
- two exact Clifford+T Toffoli depth models;
- executable restricted-key experiments preserving the complete 41-round WARP predicate;
- exact sparse-support verification;
- finite-shot and logical-noise experiments.

### Cross-cipher extension/validation
The manuscript also uses Mini-AES and S-AES as **small-domain validation experiments**, not as co-equal target ciphers.  The validation code exhaustively enumerates all 2^16 keys, checks one-pair multiplicity and two-pair uniqueness, and compares complete key-to-ciphertext occupancy spectra with the stated random-mapping baseline.

### Independent audit material
The repository includes independent numerical checks for the WARP resource chain and a bidirectional meet-in-the-middle certificate for the 10-gate S-box optimum in the declared four-qubit NCT model.

## Scope

The complete WARP Grover constructions are logical resource-estimation targets.  This repository does **not** claim that the full 381--766-qubit circuits are executable on present uncorrected NISQ hardware.

The executable full-WARP experiments restrict only the number of unknown master-key bits while preserving the complete 41-round WARP function.  Toy-WARP-8 is a separate reduced demonstrator used only for literal end-to-end Qiskit/Aer experiments and noise-sensitivity studies.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

export PYTHONPATH=$PWD/src
python tests/verify_phase6.py
python experiments/run_phase6.py
```

For the cross-cipher validation:

```bash
cd validation/cross_cipher
python saes_reference.py
python cross_cipher_collision_audit.py
```

For the independent WARP audit:

```bash
python validation/warp_core/independent_warp_numerical_audit.py
```

For the S-box optimality certificate:

```bash
g++ -O3 -std=c++17 validation/sbox_optimality/sbox_nct_mitm_certificate.cpp -o /tmp/sbox_cert
/tmp/sbox_cert
```

## Repository layout

```text
src/                         WARP core and reversible/Grover constructions
tests/                       WARP regression and sparse-support tests
experiments/                 finite-shot, logical-noise and executable experiments
validation/cross_cipher/     Mini-AES / S-AES extension and occupancy audit
validation/warp_core/        independent full-WARP numerical audit
validation/sbox_optimality/  independent 4-qubit NCT optimality certificate
data/                        generated reference outputs
manuscript/                  current manuscript source
docs/                        setup, scope, and paper-alignment notes
```

## Reproducibility and release policy

The mutable `main` branch is a development mirror.  Before journal submission, the exact submission state should be tagged (for example `v1.0-npj-submission`) and archived on Zenodo or an equivalent persistent repository.  The DOI/immutable URL should then be inserted in the manuscript Code Availability statement.

See `REPRODUCIBILITY.md` for the final release checklist.

## Citation

See `CITATION.cff`.

## License

A repository license should be selected with all coauthors before the archival release.
