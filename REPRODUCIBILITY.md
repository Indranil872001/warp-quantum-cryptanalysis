# Reproducibility checklist

Core checks included in this repository:

- full WARP official-vector and random regression tests;
- exact sparse gate-level one-/two-pair restricted-key recovery;
- balanced multi-controlled phase verification on exhaustive small instances;
- explicit preservation of all 256 branches in the u=8 full-WARP sparse test;
- finite-shot and component-noise experiments;
- second fault-tolerant resource model with T-depth-3 and T-depth-1 exact
  Toffoli decompositions.

Before public submission/release:

- [ ] Finalize the full author list in `CITATION.cff` and the manuscript.
- [ ] Select a software license with all coauthors.
- [ ] Use the public GitHub repository `Indranil872001/warp-quantum-cryptanalysis`.
- [ ] Run `./run_all.sh` in the frozen environment.
- [ ] Run the optional local Qiskit/Aer component checks.
- [ ] Freeze exact package versions (`pip freeze > environment-lock.txt`).
- [ ] Tag the submission version, e.g. `v1.0-submission`.
- [ ] Archive the tagged release on Zenodo and insert its DOI into the paper.
- [ ] Re-run the novelty/literature search immediately before submission.
