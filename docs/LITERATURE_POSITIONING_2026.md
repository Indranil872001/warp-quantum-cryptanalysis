# Literature positioning for the WARP quantum paper (checked October 2026)

## WARP-specific classical cryptanalysis

- Hadipour and Eichlseder, ToSC 2022(2): monomial-prediction / integral key
  recovery up to 32 of 41 rounds; DOI 10.46586/tosc.v2022.i2.92-112.
- Teh and Biryukov, JISA 70 (2022): differential and related-key analysis,
  including a 23-round key-recovery attack; DOI 10.1016/j.jisa.2022.103316.
- Zeng, Tan, and Xu, ToSC 2025(1): improved boomerang distinguishers and the
  first 27-round rectangle attack on WARP; DOI 10.46586/tosc.v2025.i1.444-470.
- Vaziri, 2026: automated low-data/memory meet-in-the-middle framework reports
  an 18-round WARP attack with seven known plaintexts;
  DOI 10.1007/978-3-032-15541-2_17.

## Closest quantum-resource / GFN context

- Jaques et al., EUROCRYPT 2020: full AES/LowMC Grover oracles and explicit
  width-depth optimization.
- Rahman and Paul, IEEE TQE 2022: Grover on KATAN, with exact Toffoli
  decompositions of T-depth 4/3/1, AND-gate designs, and multi-pair checking;
  DOI 10.1109/TQE.2022.3140376.
- Sun et al., EPJ Quantum Technology 2026: quantum related-key attacks on
  Feistel-like ciphers, including generic Type-1/2 GFS results under stronger
  related-key/Q2 and independent-subkey assumptions;
  DOI 10.1140/epjqt/s40507-026-00481-3.
- Ulgen, Cildiroglu, and Yayla, Physica Scripta 2026: full quantum circuit and
  three-pair Grover oracle for the hybrid GFN/ARX-SPN cipher GFSPX;
  DOI 10.1088/1402-4896/ae86c7, IACR ePrint 2026/949.

## Novelty statement we can defend

The manuscript should **not** claim that multi-pair Grover checking is new.
That idea already appears in earlier quantum-resource literature such as KATAN
and is also used by GFSPX.

The current defensible WARP-specific novelty is the combination of:

1. a verified full 41-round reversible WARP-128 implementation;
2. WARP-specific one- and two-pair oracle architectures and collision analysis
   for the equal 128-bit block/key sizes;
3. gate-, width-, and T-depth-oriented oracle variants, including a balanced
   equality tree and parallel coherent key fanout;
4. executable restricted-key experiments that preserve the full 41-round WARP
   predicate, justified by an exact sparse-support theorem;
5. finite-shot and explicitly parameterized logical-noise analysis.

A targeted search through October 2026 did not identify a prior publication
with this complete WARP-specific reversible/Grover resource analysis.  This
claim should be rechecked again immediately before submission.

## Separate stronger follow-up problem

A dedicated quantum attack on reduced-round WARP is not yet established here.
The strongest directions are:

- quantum acceleration of a subkey-recovery stage in the published 32-round
  monomial-prediction/integral framework; and
- a proof of whether WARP's concrete alternating-half key schedule satisfies or
  obstructs the assumptions of the 2026 Simon-based Type-2 GFS related-key
  construction.

These use different attack/oracle models and should not be casually mixed into
this full-round known-plaintext Grover paper without a separate derivation.
