from __future__ import annotations

from collections.abc import Sequence

import cirq
import clifft
import numpy as np

import clifft_cirq


def clifft_statevector_from_text(clifft_text: str) -> np.ndarray:
    program = clifft.compile(clifft_text)
    return np.asarray(clifft.get_statevector(program), dtype=np.complex128)


def assert_clifft_text_matches_cirq_operation(
    clifft_text: str,
    operation: cirq.Operation,
) -> None:
    """Compare an operation through one phase-insensitive Choi-state execution."""

    num_qubits = len(operation.qubits)
    system_qubits = tuple(cirq.LineQubit.range(num_qubits))
    reference_qubits = tuple(cirq.LineQubit.range(num_qubits, 2 * num_qubits))

    clifft_lines = []
    cirq_circuit = cirq.Circuit()
    for system, reference in zip(system_qubits, reference_qubits, strict=True):
        clifft_lines.extend((f"H {system.x}", f"CX {system.x} {reference.x}"))
        cirq_circuit.append((cirq.H(system), cirq.CNOT(system, reference)))

    if clifft_text:
        clifft_lines.append(clifft_text)
    cirq_circuit.append(operation.with_qubits(*system_qubits))

    assert_allclose_up_to_global_phase(
        clifft_statevector_from_text("\n".join(clifft_lines)),
        cirq.final_state_vector(
            cirq_circuit,
            qubit_order=tuple(reversed((*system_qubits, *reference_qubits))),
        ),
    )


def cirq_statevector_little_endian(
    circuit: cirq.Circuit,
    qubits: Sequence[cirq.Qid],
) -> np.ndarray:
    return cirq.final_state_vector(circuit, qubit_order=tuple(reversed(qubits)))


def clifft_statevector_for_cirq(circuit: cirq.Circuit) -> np.ndarray:
    converted = clifft_cirq.to_clifft_text(circuit)
    return clifft_statevector_from_text(converted.clifft_text)


def assert_allclose_up_to_global_phase(actual: np.ndarray, expected: np.ndarray) -> None:
    pivot = np.unravel_index(np.argmax(np.abs(expected)), expected.shape)
    if abs(actual[pivot]) > 0:
        phase = expected[pivot] / actual[pivot]
        phase /= abs(phase)
    else:
        phase = 1
    np.testing.assert_allclose(phase * actual, expected, atol=1e-7)
