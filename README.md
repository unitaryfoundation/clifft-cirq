# clifft-cirq

`clifft-cirq` converts parameter-resolved qubit `cirq.Circuit` instances into
Clifft circuit text and provides a small Cirq-style sampler facade on top of
Clifft. Parameter-resolved means the circuit has no symbolic parameters left,
for example after `cirq.resolve_parameters`.

```python
import cirq
import clifft_cirq

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(
    cirq.H(q0),
    cirq.CNOT(q0, q1),
    cirq.measure(q0, q1, key="m"),
)

converted = clifft_cirq.to_clifft_text(circuit)
print(converted.clifft_text)

sampler = clifft_cirq.ClifftSampler(seed=123)
result = sampler.run(circuit, repetitions=1000)
```

The converter returns:

- `clifft_text`: text accepted by Clifft's parser.
- `qubit_map`: the deterministic mapping from Cirq qubits to Clifft integer qubits.
- `measurement_map`: measurement-key metadata used to rebuild a `cirq.Result`.

## Supported

- Qubit circuits with parameter-resolved operations.
- Sampling behavior and measurement distributions up to unconditional global
  phase.
- Mid-circuit measurements and resets.
- Measurement keys that appear once each.
- Common one-, two-, and three-qubit gates, including `H`, Pauli gates,
  special-angle axis powers, `CX`, `CZ`, `SWAP`, `ISWAP`, `CH`, `CCX`, `CCZ`,
  and Clifft half-turn rotations such as `R_X` and `R_ZZ`.
- Operations that Cirq can decompose into supported operations.

The converter uses rotations instead of same-named Clifft sqrt gates when
Clifft and Cirq conventions differ. Unsupported operations raise
`UnsupportedCirqOperationError` with the failing operation.

## Unsupported

- Qudits.
- Unresolved symbolic parameters at the `to_clifft_text` boundary.
- Repeated measurement keys, such as `cirq.measure(q0, key="m")` followed by
  `cirq.measure(q1, key="m")`.
- Arbitrary classical control.
- Measurement confusion maps.
- Cirq noise channels.
- Device, timing, calibration, duration, and tag semantics.
- Stochastic noise, leakage, loss, and other noncomputational models.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

The package depends on `clifft>=0.5` because that release supports the gateset
used by this adapter, including controlled-gate rewrites for `CH`, `CCX`, and
`CCZ`. CI should keep testing both the Cirq floor and the latest allowed
`cirq-core<2` range.
