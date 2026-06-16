from __future__ import annotations

import types

import cirq
import numpy as np

import clifft_cirq


def test_sampler_run_uses_clifft_and_reconstructs_result(monkeypatch) -> None:
    compiled_texts: list[str] = []
    sampled: list[tuple[object, int, int | None]] = []

    def compile_stub(text: str) -> object:
        compiled_texts.append(text)
        return object()

    def sample_stub(program: object, shots: int, seed: int | None = None) -> object:
        sampled.append((program, shots, seed))
        return types.SimpleNamespace(
            measurements=np.array([[0, 1], [1, 1], [1, 0]], dtype=np.uint8)
        )

    monkeypatch.setitem(
        __import__("sys").modules,
        "clifft",
        types.SimpleNamespace(compile=compile_stub, sample=sample_stub),
    )

    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1, key="m"))

    result = clifft_cirq.ClifftSampler(seed=123).run(circuit, repetitions=3)

    assert compiled_texts == ["H 0\nCX 0 1\nM 0 1"]
    assert sampled[0][1] == 3
    assert sampled[0][2] is not None
    np.testing.assert_array_equal(
        result.measurements["m"],
        np.array([[0, 1], [1, 1], [1, 0]], dtype=np.uint8),
    )
