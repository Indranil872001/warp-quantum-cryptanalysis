# Exact sparse simulation of restricted-key reversible block-cipher oracles

## Proposition

Let `U` be any reversible classical circuit on `n` qubits composed of X, CNOT,
and Toffoli gates.  Hence `U` acts as a permutation of the computational basis.
Suppose the initial state is a superposition over only `2^u` computational-basis
states,

\[
|\psi\rangle = \sum_{a\in A} \alpha_a |a\rangle,
\qquad |A|=2^u.
\]

Then after applying `U`, the state has exactly the same support cardinality:

\[
U|\psi\rangle = \sum_{a\in A} \alpha_a |\pi_U(a)\rangle,
\]

where `pi_U` is a bijection.  Therefore `|supp(U psi)|=2^u`.

## Application to WARP

In our executable known-plaintext experiment, only `u` master-key bits are put
in superposition.  The plaintext and the remaining key bits are fixed basis
values.  The reversible WARP encryption retains the key register, so different
key candidates remain distinct basis branches throughout encryption.
Consequently, all 41 WARP rounds can be evaluated exactly by propagating only
`2^u` basis branches; a dense `2^256` statevector is unnecessary.

The phase predicate does not enlarge support.  After uncomputation, the state
returns to the key subspace, where the Grover diffuser mixes exactly the same
`2^u` candidates.  Thus a complete restricted-key Grover simulation can be
organized as:

1. build the marked set by exact reversible evaluation of each of `2^u`
   candidate branches;
2. simulate amplitudes only on the `u`-qubit key register.

## Complexity

Let `G_E` be the number of reversible logical gates in one WARP encryption and
`R` the number of Grover iterations.

- exact predicate preprocessing: `O(2^u G_E)` time;
- amplitude simulation: `O(R 2^u)` time;
- amplitude memory: `O(2^u)`;
- no dense `2^256` statevector is allocated.

For the verified WARP circuit, `G_E = 18,507` logical NCT gates.

This argument is exact for the stated restricted-key experiment; it is not an
approximation and does not imply that a full `u=128` simulation is practical.
