# WARP-128 — START HERE (Physica Scripta reviewer code archive)

**Single-click complete code/data archive:**  
https://github.com/Indranil872001/warp-quantum-cryptanalysis/archive/refs/heads/physica-scripta-reviewer-code-20261121.zip

**Underlying frozen research snapshot:** `0efcc44c4f073acd6c15c8fb8ef98c922187a2b3` (5 October 2026). All **56 original tracked research files** have been carried over unchanged. See `REVIEWER_SOURCE_MANIFEST.json` for a file-by-file Git blob checksum and size; `reviewer_check.py --verify` compares the extracted archive with that manifest.

This is a **reproducibility archive**, not a claim of actual large-scale quantum hardware execution. Main paper: *Reversible Quantum Circuits and Multi-Pair Grover Resource Analysis for WARP-128*, submitted separately to *Physica Scripta*. The older `manuscript/WARP_quantum_manuscript.tex` is a historical research manuscript and must **not** be mistaken for the submitted journal source.

## 1. Preparation

Unzip the archive, open a terminal in its top-level extracted directory, and use **Python 3.11**. An IBM Quantum account is **not required**.

Linux/macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-submission.txt
python reviewer_check.py --verify
python reviewer_check.py --smoke
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-submission.txt
python reviewer_check.py --verify
python reviewer_check.py --smoke
```

The optional C++ certificate needs a C++17 compiler (`g++`), available on Linux, macOS with compatible compiler installation, and Windows via MinGW/WSL. The recorded dependency versions are in `environment-lock.txt`; `requirements-submission.txt` specifies the intended direct dependencies. Execution logs from the reviewer runner are stored under `reviewer_results/` and **do not overwrite** the archived evidence.

## 2. One entry point, three levels of testing

| Command | Meaning |
|---|---|
| `python reviewer_check.py --verify` | Check all 56 frozen source/data files against their original Git blob hashes; independently recompute the pooled Toy-WARP noise summary, Wilson intervals and restart counts from raw CSV; verify the archived two-pair key intersections |
| `python reviewer_check.py --smoke` | In addition, compile Python sources, run WARP gate/oracle tests, balanced comparator tests, sparse-support tests, independent full-WARP audit, Toy-WARP classical/Qiskit experiments, depth resource estimates and (if `g++` is installed) the S-box certificate |
| `python reviewer_check.py --extended` | Additionally run the computationally expensive 65,536-key Mini-AES/S-AES occupancy audit with 20,000 Monte Carlo null simulations, component experiments and Qiskit small-component checks |
| `python reviewer_check.py --noise` | Additionally regenerate the final 36 replicated Toy-WARP Qiskit/Aer noise runs (12 parameter combinations × three seeds). This can be computationally demanding |

The executable suite copies the extracted repository to a temporary directory before running scripts that generate files. This preserves every checksum-verified archived result intact.

## 3. Exact research-result-to-code index

| Manuscript result | Primary code | Precomputed evidence |
|---|---|---|
| WARP-128 classical encryption and official vectors | `src/warp.py` | `data/RESULTS.txt` |
| 10-gate in-place MIDORI/WARP S-box and S-XOR | `src/midori_sbox.py`, `src/warp_quantum_round.py` | `data/RESULTS.txt` |
| Full 41-round reversible encryption and inverse | `src/warp_quantum_round.py`, `tests/verify_phase6.py` | `data/RESULTS.txt` |
| Independent WARP test-vector and numerical audit | `validation/warp_core/independent_warp_numerical_audit.py` | `validation/warp_core/INDEPENDENT_AUDIT_OUTPUT.txt` |
| 10-gate four-qubit NCT optimality certificate | `validation/sbox_optimality/sbox_nct_mitm_certificate.cpp` | `validation/sbox_optimality/SBOX_MITM_CERTIFICATE.txt` |
| One-/two-pair phase oracles, widths and gate counts | `src/grover_oracle.py`, `experiments/resource_models_v2.py` | `data/RESOURCE_MODELS_V2.csv`, `data/RESOURCE_MODELS_V2.txt` |
| Balanced comparator and coherent key fanout | `src/depth_optimized_oracle.py`, `tests/verify_depth_optimized.py` | `data/RESOURCE_MODELS_V2.csv` |
| Full-round restricted-key Grover and sparse-support proof check | `src/partial_key_grover.py`, `src/sparse_gatelevel_grover.py`, `tests/verify_sparse_support.py`, `tests/verify_phase6.py` | `data/GATELEVEL_GROVER_DEMO.json`, `data/SPARSE_SUPPORT_TEST.txt` |
| Exact ideal-cipher multiplicity/false-key law | Analytic derivation in paper/supplement; exact numerical baseline also in `validation/cross_cipher/cross_cipher_collision_audit.py` | `validation/cross_cipher/two_pair_uniqueness.csv` |
| Mini-AES and S-AES exhaustive test and occupancy null calibration | `validation/cross_cipher/cross_cipher_collision_audit.py`, `validation/cross_cipher/saes_reference.py` | `validation/cross_cipher/cross_cipher_occupancy.csv`, `validation/cross_cipher/two_pair_uniqueness.csv` |
| Finite-shot Grover statistics and fixed-confidence early stopping | `experiments/finite_shot_analysis.py`, `experiments/early_stop_tradeoff.py` | `data/FINITE_SHOT_1024.csv` |
| Logical component-noise models | `experiments/component_noise.py`, `src/noise_utils.py`, `experiments/run_phase6.py` | `data/COMPONENT_NOISE.csv` |
| Toy-WARP-8 exhaustive classical model | `experiments/toywarp8_reference.py` | Printed self-test |
| Toy-WARP-8 Qiskit full-key-space Grover circuit | `experiments/toywarp8_qiskit_end_to_end.py` | `data/GATELEVEL_GROVER_DEMO.json` is a *different*, full-WARP restricted-key demonstration |
| Toy-WARP replicated Qiskit/Aer noise campaign | `experiments/toywarp8_noise_final.py` | `data/toywarp8/QISKIT_NOISE_FINAL_RAW.csv`, `QISKIT_NOISE_FINAL_SUMMARY.csv`, `QISKIT_NOISE_FINAL_METADATA.txt`, `qiskit_noise_final.log` |
| Replot Toy-WARP noise figure | `experiments/plot_toywarp8_noise.py` | PDF regenerated into `data/toywarp8/` |
| Fresh-environment original smoke tests | `.github/workflows/reproducibility-smoke.yml` | Historical passing GitHub Actions run 37325875944 (this does not validate every optional full campaign) |

**Optional/not part of paper evidence:** `experiments/optional_ibm_hardware.py` is experimental hardware-access scaffolding; no IBM hardware run is claimed. `docs/` stores related contextual material and environment notes. The `manuscript/` folder and citation record reflect the earlier drafting stage; the journal submission files should accompany the editorial upload.

## 4. Reproduce individual results manually

```bash
# Always execute from the archive root.
export PYTHONPATH="$PWD/src:$PWD/experiments"   # Linux/macOS
python tests/verify_phase6.py
python tests/verify_depth_optimized.py
python tests/verify_sparse_support.py
python validation/warp_core/independent_warp_numerical_audit.py
python experiments/resource_models_v2.py
python experiments/toywarp8_reference.py
python experiments/toywarp8_qiskit_end_to_end.py
python experiments/plot_toywarp8_noise.py

# C++17 S-box length-optimality certificate
g++ -O3 -std=c++17 validation/sbox_optimality/sbox_nct_mitm_certificate.cpp -o sbox_certificate
./sbox_certificate
```

The runner above is preferred, because it produces separate logs without overwriting recorded results. For Mini-AES/S-AES, run `python validation/cross_cipher/cross_cipher_collision_audit.py`; for final noise, run `python experiments/toywarp8_noise_final.py`. Both may overwrite reference outputs if run **manually in place**.

## 5. Scientific and archival limitations

* The complete 128-bit WARP Grover oracles are counted as **logical circuits**; dense simulation or physical execution of the full oracle has not been shown.
* Restricted-key experiments preserve all 41 WARP rounds, but only some master-key bits vary; Toy-WARP-8 is a separate, genuinely small demonstrator.
* The software's original historical clean-environment workflow was recorded as successful; the reviewer additions were audited structurally but **not independently rerun on every platform**.
* The repository has no final coauthor-approved software license as of this archive. Public readability is not an implied open-source license.
* To make the record citable long term, publish this exact snapshot via a tagged release and Zenodo DOI (or an equivalent permanent archive) before the final journal submission.

For an unchanging reviewer link, prefer the **commit-specific archive URL** supplied in the final submission's Code Availability paragraph rather than the branch-name URL above.
