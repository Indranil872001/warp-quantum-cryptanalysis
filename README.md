# Quantum Cryptanalysis of WARP-128 with Known Plaintext

Reproducibility code for a quantum-resource and Grover key-search study of
the 128-bit lightweight block cipher WARP.

## What is implemented

- independent classical WARP-128 reference implementation;
- verified reversible 41-round WARP circuit generator;
- 10-gate WARP/MIDORI `Sb0` reversible implementation;
- clean Feistel `S(x)`-XOR construction;
- one-pair and two-pair Grover phase-oracle constructions;
- balanced-tree and coherent-key-fanout depth-oriented oracle variants;
- two exact Clifford+T Toffoli depth models (T-depth 3 and T-depth 1);
- executable restricted-key-space experiments using the full 41-round WARP
  predicate;
- exact finite-shot Grover calculations;
- an exact sparse-support theorem and full-WARP support-preservation test;
- explicitly parameterized logical Pauli-noise experiments;
- optional local Qiskit/Aer verification of small components.

## Important scope statement

The full WARP Grover oracle is a logical resource-estimation target.  The
repository does **not** claim that the full 381--766 qubit Grover circuit is
executable on current NISQ hardware.

The executable experiments keep the complete 41-round WARP encryption
function and restrict only the number of unknown master-key bits.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt

# Add src to the Python module search path
export PYTHONPATH=$PWD/src       # Windows PowerShell: $env:PYTHONPATH="$PWD\src"

python tests/verify_phase6.py
python experiments/run_phase6.py
```

## Local Qiskit/Aer

IBM Quantum access is not required for local simulation.

```bash
python experiments/qiskit_local_components.py
```

See `docs/QISKIT_LOCAL_SETUP.md`.

## Directory structure

```text
src/          core WARP and reversible/Grover constructions
tests/        regression, balanced-comparator, and sparse-support tests
experiments/  finite-shot, noise, and Qiskit scripts
data/         generated reference outputs
manuscript/   current LaTeX manuscript source
docs/         setup and paper-alignment notes
```

## Reproducibility

The main regression suite checks:

- official WARP test vectors;
- reversible circuit correctness;
- exact sparse gate-level known-plaintext predicate;
- one- and two-pair restricted-key Grover recovery;
- exact finite-shot calculations.

## Citation

A `CITATION.cff` file should be finalized with the complete author list and
paper title before public release.

## License

Choose the repository license together with all coauthors before public
release.  No license is asserted by this preparation package.
