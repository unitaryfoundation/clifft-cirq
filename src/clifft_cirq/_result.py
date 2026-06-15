"""Mapping Clifft sample matrices back to Cirq results."""

from __future__ import annotations

from collections.abc import Mapping

import cirq
import numpy as np
import numpy.typing as npt

from clifft_cirq._convert import ConvertedCircuit


def result_dict_from_clifft_samples(
    converted: ConvertedCircuit,
    measurements: npt.ArrayLike,
    *,
    params: cirq.ParamResolverOrSimilarType | None = None,
) -> cirq.ResultDict:
    """Build a `cirq.ResultDict` from Clifft measurement columns."""

    measurement_array = np.asarray(measurements, dtype=np.uint8)
    if measurement_array.ndim != 2:
        raise ValueError("Clifft measurements must be a 2D array")

    expected_columns = _expected_measurement_columns(converted)
    if measurement_array.shape[1] != expected_columns:
        raise ValueError(
            f"Clifft returned {measurement_array.shape[1]} measurement columns, "
            f"expected {expected_columns}"
        )

    cirq_measurements: Mapping[str, npt.NDArray[np.uint8]] = {
        key: measurement_array[:, metadata.columns].astype(np.uint8, copy=False)
        for key, metadata in converted.measurement_map.items()
    }
    return cirq.ResultDict(
        params=cirq.ParamResolver({} if params is None else params),
        measurements=cirq_measurements,
    )


def _expected_measurement_columns(converted: ConvertedCircuit) -> int:
    if not converted.measurement_map:
        return 0
    columns = (
        column
        for metadata in converted.measurement_map.values()
        for column in metadata.columns
    )
    return max(columns) + 1
