# Paper-alignment matrix: Mini-AES npj paper -> WARP project

The uploaded reference paper ("Quantum cryptanalysis of SPN ciphers with known
plaintext", npj Quantum Information, 2026) is used as a methodological
benchmark, not as a template to copy verbatim.

| Reference-paper element | WARP counterpart | Status |
|---|---|---|
| Complete quantum implementation of cipher modules | Full 41-round reversible WARP-128 circuit | DONE |
| Nonlinear module optimization | 10-gate MIDORI/WARP Sb0; verified optimal NCT count in our model | DONE |
| Component-wise noise | Sb0, S-XOR, key addition, complete round logical-noise study | DONE in Phase 6 |
| Known-plaintext Grover recovery | Full-WARP partial-key-space Grover recovery | DONE |
| Actual circuit-level predicate validation | Sparse exact simulation using the full 41-round NCT circuit | DONE in Phase 6 |
| Full oracle resource estimation | One-pair and three two-pair architectures | DONE |
| Key clustering / multiple valid keys | Collision-aware ideal-cipher analysis; one pair does not imply weakness | DONE, stronger treatment |
| Reduced executable instance | Restricted unknown-key subspace of full WARP instead of inventing a new toy cipher | DONE |
| Optimal Grover iterations | Exact formula + executable curves | DONE |
| Finite-shot analysis | Exact binomial finite-shot analysis at 1024 shots | DONE in Phase 6 |
| Noise-aware iteration choice | Fixed-success repetition cost under explicit local-Pauli proxy | DONE |
| Realistic/NISQ discussion | Explicit no-fault sanity proxy; no claim full WARP is NISQ-executable | DONE |
| Qiskit implementation | Small-component local Aer scripts + full circuit builder from earlier phases | READY |
| IBM-QPU execution | Optional small-component validation only | OPTIONAL, not required |

## Important methodological improvements over the reference paper

1. **Collision interpretation.**
   Multiple keys for one plaintext/ciphertext pair are expected when key size
   equals block size.  We therefore do not label this automatically as a WARP
   weakness.

2. **Two-pair oracle.**
   We construct an AND predicate over two independent known pairs so the
   master key is unique with overwhelming probability under the ideal-cipher
   model.

3. **Grover iteration optimization.**
   We distinguish "fewer iterations per run" from lower fixed-success total
   cost by accounting for repetitions.

4. **Noise claims.**
   We do not equate a simulator noise model with evidence that the full attack
   is hardware-feasible.

5. **Full cipher rather than a new toy variant.**
   Executable experiments restrict the unknown-key subspace but retain the
   complete 41-round WARP encryption function.
