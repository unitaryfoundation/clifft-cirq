# Release Process

This repository publishes `clifft-cirq` to PyPI through GitHub Actions.
Releases are driven by version tags like `v0.1.0`.

## Local prerequisites

Release preparation uses:

- `uv` for Python environment and package builds.
- `just` for release helper commands.
- `git-cliff` for changelog generation.

## Cut a release

1. Start from an up-to-date `main` branch:

   ```bash
   git checkout main
   git pull --ff-only origin main
   ```

2. Pick the next semantic version and preview the generated changelog:

   ```bash
   just changelog-preview v0.1.0
   ```

3. Generate the changelog entry:

   ```bash
   just changelog v0.1.0
   ```

4. Edit `CHANGELOG.md`. Keep the generated grouped bullets, but add a short
   human-written summary for the release when useful.

   The first `0.1.0` release may need a hand-written entry because the initial
   scaffold PR was merged before squash-only conventional PR titles were
   enforced. Future releases should be generated from squash commit titles.

5. Open and merge a release-prep PR containing the changelog update.

6. Tag the release from the merged `main` branch:

   ```bash
   git checkout main
   git pull --ff-only origin main
   git tag v0.1.0
   git push origin v0.1.0
   ```

7. Watch the `Release` workflow. It should:

   - build an sdist and wheel
   - publish to TestPyPI
   - publish to PyPI
   - create a GitHub Release using the matching `CHANGELOG.md` section

8. Verify the published package from a clean environment:

   ```bash
   uv venv /tmp/clifft-cirq-release-smoke
   /tmp/clifft-cirq-release-smoke/bin/python -m pip install -U pip
   /tmp/clifft-cirq-release-smoke/bin/python -m pip install clifft-cirq
   /tmp/clifft-cirq-release-smoke/bin/python - <<'PY'
   import cirq
   import clifft_cirq

   q0, q1 = cirq.LineQubit.range(2)
   circuit = cirq.Circuit(
       cirq.H(q0),
       cirq.CNOT(q0, q1),
       cirq.measure(q0, q1, key="m"),
   )
   result = clifft_cirq.ClifftSampler(seed=123).run(circuit, repetitions=4)
   print(clifft_cirq.__version__)
   print(result)
   PY
   ```

## TestPyPI dry run

Use the manual `Release` workflow dispatch for TestPyPI-only dry runs. Provide
a version like `0.1.0.dev1`. Manual dispatch never publishes to PyPI and never
creates a GitHub Release.

## Failure handling

If publishing fails before PyPI, fix the issue and rerun the workflow. If PyPI
publishing succeeds but GitHub Release creation fails, rerun the failed job or
create the GitHub Release manually from the same tag using the matching
`CHANGELOG.md` section.
