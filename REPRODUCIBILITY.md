# Reproducibility checklist

## WARP core checks already represented in this repository

- complete WARP official-vector and random regression tests;
- verified reversible 41-round encryption;
- exact sparse one-/two-pair restricted-key recovery;
- balanced multi-controlled phase verification on exhaustive small instances;
- preservation of all 256 branches in the u=8 full-WARP sparse test;
- finite-shot and logical component-noise experiments;
- two fault-tolerant Toffoli depth models.

## New manuscript-specific validation material

The current manuscript additionally relies on:

- exact ideal-cipher known-plaintext identifiability calculations;
- Mini-AES and S-AES exhaustive 2^16-key cross-cipher validation;
- a pre-declared 16-plaintext-per-cipher occupancy experiment with 20,000 random-mapping Monte Carlo calibrations;
- an independent WARP numerical audit;
- an independent 4-qubit NCT bidirectional certificate excluding S-box circuits of length <= 9;
- Toy-WARP-8 full-key Qiskit/Aer experiments and the final three-seed depolarizing campaign.

These files should remain in the repository and in the frozen journal release.

## Before pressing Submit

- [x] Update the manuscript source in `manuscript/`.
- [x] Update `CITATION.cff` with Indranil Mukherjee and Bimal Mandal.
- [x] Add cross-cipher Mini-AES/S-AES validation code and outputs.
- [x] Add the independent WARP numerical audit.
- [x] Add the S-box optimality certificate.
- [x] Add the final Toy-WARP-8 execution scripts, raw replicated CSV, summary, metadata, and execution log.
- [ ] Run `./run_all.sh` in the final environment.
- [ ] Freeze exact Python/package versions: `python -m pip freeze > environment-lock.txt`.
- [ ] Select a software license with all coauthors.
- [ ] Tag the submission state, e.g. `v1.0-npj-submission`.
- [ ] Archive the tag on Zenodo/OSF or an equivalent persistent repository.
- [ ] Insert the persistent DOI/immutable URL in the manuscript Code Availability statement.
- [ ] Re-run the literature/novelty search immediately before submission.

## Public repository

https://github.com/Indranil872001/warp-quantum-cryptanalysis
