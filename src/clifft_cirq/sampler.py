"""Cirq-style sampler facade backed by Clifft."""

from __future__ import annotations

import cirq
import numpy as np

from clifft_cirq._convert import to_clifft_text
from clifft_cirq._result import result_dict_from_clifft_samples


class ClifftSampler(cirq.Sampler):
    """Sample Cirq circuits through Clifft."""

    def __init__(self, seed: cirq.RANDOM_STATE_OR_SEED_LIKE = None) -> None:
        self._rng = None if seed is None else np.random.default_rng(seed)

    def run(
        self,
        program: cirq.AbstractCircuit,
        param_resolver: cirq.ParamResolverOrSimilarType | None = None,
        repetitions: int = 1,
    ) -> cirq.Result:
        """Resolve, convert, and sample one Cirq circuit with Clifft.

        Args:
            program: Cirq circuit to sample.
            param_resolver: Optional parameter resolver applied before
                conversion.
            repetitions: Number of shots to sample.

        Returns:
            A `cirq.Result` with measurement arrays keyed like the input
            circuit.
        """

        resolved = cirq.resolve_parameters(program, cirq.ParamResolver(param_resolver or {}))
        converted = to_clifft_text(resolved)

        # Keep plain `import clifft_cirq` usable for converter-only callers without
        # importing the Clifft extension or running its CPU checks.
        import clifft

        compiled = clifft.compile(converted.clifft_text)
        seed = self._next_seed()
        if seed is None:
            sample_result = clifft.sample(compiled, shots=repetitions)
        else:
            sample_result = clifft.sample(compiled, shots=repetitions, seed=seed)
        return result_dict_from_clifft_samples(
            converted,
            sample_result.measurements,
            params=param_resolver,
        )

    def run_sweep(
        self,
        program: cirq.AbstractCircuit,
        params: cirq.Sweepable = None,
        repetitions: int = 1,
    ) -> list[cirq.Result]:
        """Sample one circuit for each resolver in a Cirq sweep.

        Args:
            program: Cirq circuit to sample.
            params: Cirq sweepable parameter values.
            repetitions: Number of shots to sample per resolver.

        Returns:
            One `cirq.Result` per resolver produced by `cirq.to_resolvers`.
        """

        resolvers = cirq.to_resolvers(params)
        return [
            self.run(program, param_resolver=resolver, repetitions=repetitions)
            for resolver in resolvers
        ]

    def _run(
        self,
        circuit: cirq.AbstractCircuit,
        param_resolver: cirq.ParamResolver,
        repetitions: int,
    ) -> dict[str, np.ndarray]:
        result = self.run(circuit, param_resolver=param_resolver, repetitions=repetitions)
        return dict(result.measurements)

    def _next_seed(self) -> int | None:
        if self._rng is None:
            return None
        return int(self._rng.integers(0, np.iinfo(np.int64).max))
