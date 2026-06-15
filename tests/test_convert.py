from __future__ import annotations

import cirq
import numpy as np
import pytest
import sympy
from _helpers import (
    assert_allclose_up_to_global_phase,
    cirq_little_endian_unitary,
    clifft_unitary_from_text,
)

import clifft_cirq
from clifft_cirq._result import result_dict_from_clifft_samples


def test_direct_gates_and_measurement_metadata() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.CNOT(q0, q1),
        cirq.measure(q0, q1, key="m", invert_mask=(True, False)),
    )

    converted = clifft_cirq.to_clifft_text(circuit)

    assert converted.clifft_text == "H 0\nCX 0 1\nM !0 1"
    assert converted.qubit_map == {q0: 0, q1: 1}
    assert converted.measurement_map["m"].columns == (0, 1)
    assert converted.measurement_map["m"].invert_mask == (True, False)


def test_special_angle_canonicalization() -> None:
    q = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.XPowGate(exponent=0.5)(q),
        cirq.XPowGate(exponent=-0.5)(q),
        cirq.YPowGate(exponent=0.5)(q),
        cirq.ZPowGate(exponent=0.5)(q),
        cirq.ZPowGate(exponent=0.25)(q),
        cirq.XPowGate(exponent=0)(q),
        cirq.rx(np.pi / 3)(q),
    )

    converted = clifft_cirq.to_clifft_text(circuit)

    assert converted.clifft_text.splitlines() == [
        "R_X(0.5) 0",
        "R_X(-0.5) 0",
        "R_Y(0.5) 0",
        "S 0",
        "T 0",
        "R_X(0.333333333333) 0",
    ]


def test_two_qubit_special_angles_and_rotations() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.XXPowGate(exponent=0.5)(q0, q1),
        cirq.YYPowGate(exponent=-0.5)(q0, q1),
        cirq.ZZPowGate(exponent=0.25)(q0, q1),
    )

    converted = clifft_cirq.to_clifft_text(circuit)

    assert converted.clifft_text.splitlines() == [
        "R_XX(0.5) 0 1",
        "R_YY(-0.5) 0 1",
        "R_ZZ(0.25) 0 1",
    ]


@pytest.mark.parametrize(
    ("operation_factory", "expected_text"),
    [
        (lambda q: cirq.XPowGate(exponent=0.5)(q), "R_X(0.5) 0"),
        (lambda q: cirq.XPowGate(exponent=-0.5)(q), "R_X(-0.5) 0"),
        (lambda q: cirq.YPowGate(exponent=0.5)(q), "R_Y(0.5) 0"),
        (lambda q: cirq.YPowGate(exponent=-0.5)(q), "R_Y(-0.5) 0"),
        (lambda q: cirq.ZPowGate(exponent=0.5)(q), "S 0"),
        (lambda q: cirq.ZPowGate(exponent=-0.5)(q), "S_DAG 0"),
        (lambda q: cirq.ZPowGate(exponent=0.25)(q), "T 0"),
        (lambda q: cirq.ZPowGate(exponent=-0.25)(q), "T_DAG 0"),
    ],
)
def test_single_qubit_special_angles_match_cirq_unitary(
    operation_factory,
    expected_text: str,
) -> None:
    q = cirq.LineQubit(0)
    operation = operation_factory(q)
    converted = clifft_cirq.to_clifft_text(cirq.Circuit(operation))

    assert converted.clifft_text == expected_text
    assert_allclose_up_to_global_phase(
        clifft_unitary_from_text(converted.clifft_text, num_qubits=1),
        cirq_little_endian_unitary(operation),
    )


@pytest.mark.parametrize(
    ("operation_factory", "expected_text"),
    [
        (lambda q0, q1: cirq.XXPowGate(exponent=0.5)(q0, q1), "R_XX(0.5) 0 1"),
        (lambda q0, q1: cirq.XXPowGate(exponent=-0.5)(q0, q1), "R_XX(-0.5) 0 1"),
        (lambda q0, q1: cirq.YYPowGate(exponent=0.5)(q0, q1), "R_YY(0.5) 0 1"),
        (lambda q0, q1: cirq.YYPowGate(exponent=-0.5)(q0, q1), "R_YY(-0.5) 0 1"),
        (lambda q0, q1: cirq.ZZPowGate(exponent=0.5)(q0, q1), "R_ZZ(0.5) 0 1"),
        (lambda q0, q1: cirq.ZZPowGate(exponent=-0.5)(q0, q1), "R_ZZ(-0.5) 0 1"),
    ],
)
def test_two_qubit_special_angles_match_cirq_unitary(
    operation_factory,
    expected_text: str,
) -> None:
    q0, q1 = cirq.LineQubit.range(2)
    operation = operation_factory(q0, q1)
    converted = clifft_cirq.to_clifft_text(cirq.Circuit(operation))

    assert converted.clifft_text == expected_text
    assert_allclose_up_to_global_phase(
        clifft_unitary_from_text(converted.clifft_text, num_qubits=2),
        cirq_little_endian_unitary(operation),
    )


@pytest.mark.parametrize(
    ("operation_factory", "expected_text", "num_qubits"),
    [
        (lambda q: cirq.CNOT(q[0], q[1]), "CX 0 1", 2),
        (lambda q: cirq.CZ(q[0], q[1]), "CZ 0 1", 2),
        (lambda q: cirq.SWAP(q[0], q[1]), "SWAP 0 1", 2),
        (lambda q: cirq.ISWAP(q[0], q[1]), "ISWAP 0 1", 2),
        (lambda q: cirq.ISwapPowGate(exponent=-1)(q[0], q[1]), "ISWAP_DAG 0 1", 2),
        (lambda q: cirq.ControlledGate(cirq.H)(q[0], q[1]), "CH 0 1", 2),
        (lambda q: cirq.CCX(q[0], q[1], q[2]), "CCX 0 1 2", 3),
        (lambda q: cirq.CCZ(q[0], q[1], q[2]), "CCZ 0 1 2", 3),
    ],
)
def test_native_direct_gates_match_cirq_unitary(
    operation_factory,
    expected_text: str,
    num_qubits: int,
) -> None:
    qubits = cirq.LineQubit.range(num_qubits)
    operation = operation_factory(qubits)
    converted = clifft_cirq.to_clifft_text(cirq.Circuit(operation))

    assert converted.clifft_text == expected_text
    assert_allclose_up_to_global_phase(
        clifft_unitary_from_text(converted.clifft_text, num_qubits=num_qubits),
        cirq_little_endian_unitary(operation),
    )


def test_controlled_h_with_nontrivial_subgate_global_phase_does_not_emit_plain_ch() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    operation = cirq.ControlledGate(
        cirq.HPowGate(exponent=1, global_shift=0.5),
    )(q0, q1)

    converted = clifft_cirq.to_clifft_text(cirq.Circuit(operation))

    assert converted.clifft_text != "CH 0 1"
    assert_allclose_up_to_global_phase(
        clifft_unitary_from_text(converted.clifft_text, num_qubits=2),
        cirq_little_endian_unitary(operation),
    )


def test_default_and_explicit_qubit_order_are_stable() -> None:
    q0 = cirq.LineQubit(0)
    q2 = cirq.LineQubit(2)
    circuit = cirq.Circuit(cirq.CNOT(q2, q0))

    default_converted = clifft_cirq.to_clifft_text(circuit)
    explicit_converted = clifft_cirq.to_clifft_text(circuit, qubit_order=[q2, q0])

    assert default_converted.qubit_map == {q0: 0, q2: 1}
    assert default_converted.clifft_text == "CX 1 0"
    assert explicit_converted.qubit_map == {q2: 0, q0: 1}
    assert explicit_converted.clifft_text == "CX 0 1"


def test_global_phase_operation_is_ignored() -> None:
    q = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.H(q),
        cirq.global_phase_operation(1j),
        cirq.measure(q, key="m"),
    )

    converted = clifft_cirq.to_clifft_text(circuit)

    assert converted.clifft_text == "H 0\nM 0"


def test_measurement_result_mapping_preserves_columns_without_double_flipping() -> None:
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.measure(q0, key="a", invert_mask=(True,)),
        cirq.measure(q1, q0, key="b"),
    )
    converted = clifft_cirq.to_clifft_text(circuit)
    samples = np.array([[1, 0, 1], [0, 1, 1]], dtype=np.uint8)

    result = result_dict_from_clifft_samples(converted, samples)

    np.testing.assert_array_equal(result.measurements["a"], np.array([[1], [0]], dtype=np.uint8))
    np.testing.assert_array_equal(
        result.measurements["b"],
        np.array([[0, 1], [1, 1]], dtype=np.uint8),
    )


def test_repeated_measurement_key_is_rejected() -> None:
    q = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.measure(q, key="m"), cirq.measure(q, key="m"))

    with pytest.raises(clifft_cirq.UnsupportedCirqOperationError, match="repeated measurement key"):
        clifft_cirq.to_clifft_text(circuit)


def test_measurement_confusion_map_is_rejected() -> None:
    q = cirq.LineQubit(0)
    gate = cirq.MeasurementGate(
        1,
        key="m",
        confusion_map={(0,): np.array([[0.0, 1.0], [1.0, 0.0]])},
    )
    circuit = cirq.Circuit(gate(q))

    with pytest.raises(clifft_cirq.UnsupportedCirqOperationError, match="confusion_map"):
        clifft_cirq.to_clifft_text(circuit)


def test_noise_channels_are_rejected() -> None:
    q = cirq.LineQubit(0)
    circuits = [
        cirq.Circuit(cirq.bit_flip(1.0)(q)),
        cirq.Circuit(cirq.depolarize(0.1)(q)),
    ]

    for circuit in circuits:
        with pytest.raises(clifft_cirq.UnsupportedCirqOperationError):
            clifft_cirq.to_clifft_text(circuit)


def test_classically_controlled_operation_is_rejected() -> None:
    q = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.measure(q, key="m"),
        cirq.X(q).with_classical_controls("m"),
    )

    with pytest.raises(clifft_cirq.UnsupportedCirqOperationError):
        clifft_cirq.to_clifft_text(circuit)


def test_qudits_are_rejected() -> None:
    q = cirq.LineQid(0, dimension=3)
    circuit = cirq.Circuit(cirq.IdentityGate(qid_shape=(3,)).on(q))

    with pytest.raises(ValueError, match="only supports qubits"):
        clifft_cirq.to_clifft_text(circuit)


def test_unresolved_parameters_are_rejected() -> None:
    q = cirq.LineQubit(0)
    theta = sympy.Symbol("theta")
    circuit = cirq.Circuit(cirq.rx(theta)(q))

    with pytest.raises(ValueError, match="resolved"):
        clifft_cirq.to_clifft_text(circuit)


def test_reset_emits_reset_gate() -> None:
    q = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.reset(q))

    assert clifft_cirq.to_clifft_text(circuit).clifft_text == "R 0"
