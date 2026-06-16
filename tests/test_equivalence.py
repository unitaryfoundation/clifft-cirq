from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence

import cirq
import clifft
import numpy as np
from _helpers import (
    assert_allclose_up_to_global_phase,
    cirq_statevector_little_endian,
    clifft_statevector_for_cirq,
)

import clifft_cirq


def _joint_counts(result: cirq.Result, keys: Sequence[str]) -> Counter[tuple[int, ...]]:
    repetitions = next(iter(result.measurements.values())).shape[0]
    counts: Counter[tuple[int, ...]] = Counter()
    for row in range(repetitions):
        bits: list[int] = []
        for key in keys:
            bits.extend(int(bit) for bit in result.measurements[key][row])
        counts[tuple(bits)] += 1
    return counts


def _assert_distribution_close(
    actual: Counter[tuple[int, ...]],
    expected: Counter[tuple[int, ...]],
    shots: int,
    *,
    atol: float,
) -> None:
    outcomes = set(actual) | set(expected)
    for outcome in outcomes:
        actual_probability = actual[outcome] / shots
        expected_probability = expected[outcome] / shots
        assert abs(actual_probability - expected_probability) <= atol, (
            outcome,
            actual_probability,
            expected_probability,
        )


def _random_unitary_circuit(seed: int, num_qubits: int, depth: int) -> cirq.Circuit:
    rng = np.random.default_rng(seed)
    qubits = cirq.LineQubit.range(num_qubits)
    circuit = cirq.Circuit(cirq.H.on_each(*qubits))

    single_qubit_factories: tuple[Callable[[cirq.Qid], cirq.Operation], ...] = (
        cirq.H,
        cirq.X,
        cirq.Y,
        cirq.Z,
        cirq.S,
        cirq.T,
        lambda q: cirq.XPowGate(exponent=0.3)(q),
        lambda q: cirq.YPowGate(exponent=-0.4)(q),
        lambda q: cirq.ZPowGate(exponent=0.35)(q),
    )
    two_qubit_factories: tuple[Callable[[cirq.Qid, cirq.Qid], cirq.Operation], ...] = (
        cirq.CNOT,
        cirq.CZ,
        lambda a, b: cirq.XXPowGate(exponent=0.5)(a, b),
        lambda a, b: cirq.YYPowGate(exponent=-0.3)(a, b),
        lambda a, b: cirq.ZZPowGate(exponent=0.25)(a, b),
    )

    for _ in range(depth):
        if num_qubits == 1 or rng.random() < 0.65:
            qubit = qubits[int(rng.integers(num_qubits))]
            factory = single_qubit_factories[int(rng.integers(len(single_qubit_factories)))]
            circuit.append(factory(qubit))
        else:
            a, b = rng.choice(num_qubits, size=2, replace=False)
            factory = two_qubit_factories[int(rng.integers(len(two_qubit_factories)))]
            circuit.append(factory(qubits[int(a)], qubits[int(b)]))

    return circuit


def test_bell_sampler_distribution_matches_cirq() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1, key="m"))
    shots = 1000

    clifft_result = clifft_cirq.ClifftSampler(seed=123).run(circuit, repetitions=shots)
    cirq_result = cirq.Simulator(seed=456).run(circuit, repetitions=shots)
    clifft_counts = _joint_counts(clifft_result, ["m"])
    cirq_counts = _joint_counts(cirq_result, ["m"])

    assert set(clifft_counts) <= {(0, 0), (1, 1)}
    assert set(cirq_counts) <= {(0, 0), (1, 1)}
    assert 0.35 <= clifft_counts[(0, 0)] / shots <= 0.65
    assert 0.35 <= cirq_counts[(0, 0)] / shots <= 0.65
    _assert_distribution_close(clifft_counts, cirq_counts, shots, atol=0.12)


def test_ghz_sampler_distribution_matches_cirq() -> None:
    q0, q1, q2 = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.CNOT(q0, q1),
        cirq.CNOT(q1, q2),
        cirq.measure(q0, q1, q2, key="m"),
    )
    shots = 1000

    clifft_result = clifft_cirq.ClifftSampler(seed=1234).run(circuit, repetitions=shots)
    cirq_result = cirq.Simulator(seed=5678).run(circuit, repetitions=shots)
    clifft_counts = _joint_counts(clifft_result, ["m"])
    cirq_counts = _joint_counts(cirq_result, ["m"])

    assert set(clifft_counts) <= {(0, 0, 0), (1, 1, 1)}
    assert set(cirq_counts) <= {(0, 0, 0), (1, 1, 1)}
    assert 0.35 <= clifft_counts[(0, 0, 0)] / shots <= 0.65
    assert 0.35 <= cirq_counts[(0, 0, 0)] / shots <= 0.65
    _assert_distribution_close(clifft_counts, cirq_counts, shots, atol=0.12)


def test_deterministic_invert_mask_matches_cirq() -> None:
    q = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.X(q), cirq.measure(q, key="m", invert_mask=(True,)))

    clifft_result = clifft_cirq.ClifftSampler(seed=10).run(circuit, repetitions=8)
    cirq_result = cirq.Simulator(seed=11).run(circuit, repetitions=8)

    np.testing.assert_array_equal(clifft_result.measurements["m"], np.zeros((8, 1), dtype=np.uint8))
    np.testing.assert_array_equal(clifft_result.measurements["m"], cirq_result.measurements["m"])


def test_interleaved_measurement_keys_match_cirq() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.X(q0),
        cirq.measure(q1, key="b"),
        cirq.measure(q0, q1, key="a"),
    )

    clifft_result = clifft_cirq.ClifftSampler(seed=12).run(circuit, repetitions=5)
    cirq_result = cirq.Simulator(seed=13).run(circuit, repetitions=5)

    np.testing.assert_array_equal(clifft_result.measurements["b"], cirq_result.measurements["b"])
    np.testing.assert_array_equal(clifft_result.measurements["a"], cirq_result.measurements["a"])
    np.testing.assert_array_equal(clifft_result.measurements["b"], np.zeros((5, 1), dtype=np.uint8))
    np.testing.assert_array_equal(
        clifft_result.measurements["a"],
        np.array([[1, 0]] * 5, dtype=np.uint8),
    )


def test_mid_circuit_measurement_distribution_matches_cirq() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.measure(q0, key="m0"),
        cirq.CNOT(q0, q1),
        cirq.measure(q1, key="m1"),
    )
    shots = 2000

    clifft_result = clifft_cirq.ClifftSampler(seed=14).run(circuit, repetitions=shots)
    cirq_result = cirq.Simulator(seed=15).run(circuit, repetitions=shots)
    clifft_counts = _joint_counts(clifft_result, ["m0", "m1"])
    cirq_counts = _joint_counts(cirq_result, ["m0", "m1"])

    assert set(clifft_counts) <= {(0, 0), (1, 1)}
    assert set(cirq_counts) <= {(0, 0), (1, 1)}
    _assert_distribution_close(clifft_counts, cirq_counts, shots, atol=0.08)


def test_random_small_unitary_circuits_match_cirq_statevector() -> None:
    for seed in range(20):
        num_qubits = 1 + seed % 3
        qubits = cirq.LineQubit.range(num_qubits)
        circuit = _random_unitary_circuit(seed=seed, num_qubits=num_qubits, depth=7)

        assert_allclose_up_to_global_phase(
            clifft_statevector_for_cirq(circuit),
            cirq_statevector_little_endian(circuit, qubits),
        )


def test_random_sampled_circuits_match_cirq_distribution() -> None:
    shots = 2000
    for seed in range(10):
        num_qubits = 2 + seed % 2
        qubits = cirq.LineQubit.range(num_qubits)
        circuit = _random_unitary_circuit(seed=100 + seed, num_qubits=num_qubits, depth=6)
        circuit.append(cirq.measure(*qubits, key="m"))

        clifft_result = clifft_cirq.ClifftSampler(seed=200 + seed).run(
            circuit,
            repetitions=shots,
        )
        cirq_result = cirq.Simulator(seed=300 + seed).run(circuit, repetitions=shots)

        _assert_distribution_close(
            _joint_counts(clifft_result, ["m"]),
            _joint_counts(cirq_result, ["m"]),
            shots,
            atol=0.08,
        )


def test_representative_supported_circuit_compiles() -> None:
    q0, q1, q2 = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.T(q0),
        cirq.XPowGate(exponent=0.3)(q1),
        cirq.CNOT(q0, q1),
        cirq.CCZ(q0, q1, q2),
        cirq.measure(q0, q1, q2, key="m"),
    )

    converted = clifft_cirq.to_clifft_text(circuit)
    program = clifft.compile(converted.clifft_text)

    assert program.num_measurements == 3


def test_clifford_pow_circuit_compiles_to_zero_peak_rank() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.XPowGate(exponent=0.5)(q0),
        cirq.YPowGate(exponent=-0.5)(q1),
        cirq.CXPowGate(exponent=1)(q0, q1),
        cirq.ZPowGate(exponent=0.5)(q0),
    )

    converted = clifft_cirq.to_clifft_text(circuit)
    program = clifft.compile(converted.clifft_text)

    assert program.peak_rank == 0
