from __future__ import annotations

from collections.abc import Sequence

import cirq
import clifft
import numpy as np

import clifft_cirq


def clifft_statevector_from_text(clifft_text: str) -> np.ndarray:
    program = clifft.compile(clifft_text)
    state = clifft.State(
        peak_rank=program.peak_rank,
        num_measurements=program.num_measurements,
    )
    clifft.execute(program, state)
    return np.asarray(clifft.get_statevector(program, state), dtype=np.complex128)


def clifft_unitary_from_text(clifft_text: str, num_qubits: int) -> np.ndarray:
    """Build a Clifft unitary by executing the program on every basis state."""

    columns = []
    for basis in range(2**num_qubits):
        prep = [f"X {qubit}" for qubit in range(num_qubits) if (basis >> qubit) & 1]
        lines = [*prep]
        if clifft_text:
            lines.append(clifft_text)
        columns.append(clifft_statevector_from_text("\n".join(lines)))
    return np.column_stack(columns)


def cirq_little_endian_unitary(operation: cirq.Operation) -> np.ndarray:
    qubits = tuple(operation.qubits)
    circuit = cirq.Circuit(operation)
    columns = []
    for basis in range(2 ** len(qubits)):
        initial_state = np.zeros(2 ** len(qubits), dtype=np.complex128)
        initial_state[basis] = 1
        columns.append(
            cirq.final_state_vector(
                circuit,
                initial_state=initial_state,
                qubit_order=tuple(reversed(qubits)),
            )
        )
    return np.column_stack(columns)


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
