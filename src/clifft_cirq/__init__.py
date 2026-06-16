"""Cirq adapter for Clifft circuit text and sampling."""

from importlib import metadata

from clifft_cirq._convert import (
    ConvertedCircuit,
    MeasurementMetadata,
    UnsupportedCirqOperationError,
    to_clifft_text,
)
from clifft_cirq.sampler import ClifftSampler

__all__ = [
    "ClifftSampler",
    "ConvertedCircuit",
    "MeasurementMetadata",
    "UnsupportedCirqOperationError",
    "to_clifft_text",
]

try:
    __version__ = metadata.version("clifft-cirq")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
