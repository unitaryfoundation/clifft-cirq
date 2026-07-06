# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-07-06

### Bug Fixes

- support Cirq 1.7 CZ decompositions (#4) by @bachase in [#4](https://github.com/unitaryfoundation/clifft-cirq/pull/4)

### CI

- preserve Cirq matrix overrides (#5) by @bachase in [#5](https://github.com/unitaryfoundation/clifft-cirq/pull/5)

## [0.1.0] - 2026-06-16

This is the first public release of `clifft-cirq`, a lightweight Cirq adapter
for Clifft. It converts supported parameter-resolved qubit `cirq.Circuit`
instances to Clifft circuit text and provides `ClifftSampler`, a Cirq-style
sampler facade backed by Clifft.

The initial adapter focuses on convention-tested correctness for common
unitary gates, terminal and mid-circuit measurements, resets, measurement-key
result mapping, invert masks, and supported Cirq decompositions. Unsupported
semantics such as qudits, unresolved parameters, repeated measurement keys,
measurement confusion maps, noise channels, and arbitrary classical control are
rejected explicitly.

### Features

- scaffold Cirq-to-Clifft conversion and sampler APIs by @bachase in [#1](https://github.com/unitaryfoundation/clifft-cirq/pull/1)
- add package release process, changelog tooling, and TestPyPI/PyPI publishing workflow by @bachase in [#2](https://github.com/unitaryfoundation/clifft-cirq/pull/2)

### Testing

- add converter and sampler equivalence coverage against Cirq and Clifft by @bachase in [#1](https://github.com/unitaryfoundation/clifft-cirq/pull/1)
- add installed-wheel package checks to CI and release builds by @bachase in [#2](https://github.com/unitaryfoundation/clifft-cirq/pull/2)
