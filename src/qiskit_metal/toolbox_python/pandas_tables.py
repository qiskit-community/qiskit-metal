# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Concatenate qgeometry tables with the pandas 2 result dtypes.

Imports only pandas, so modules low in the import graph
(``toolbox_metal``, ``qgeometries``, the renderers) can use it without
importing ``qiskit_metal.draw`` and closing an import cycle.
"""

import pandas as pd

__all__ = ["concat_tables"]


def _holds_na(dtype) -> bool:
    """True if a column of ``dtype`` can hold a missing value."""
    if isinstance(dtype, pd.api.extensions.ExtensionDtype):
        return True
    return dtype.kind in "fcmMO"


def concat_tables(frames: list, **kwargs) -> pd.DataFrame:
    """``pd.concat(frames, **kwargs)`` along the rows, with the result dtypes
    of pandas 2 on every pandas version.

    pandas 2 leaves a column that is empty or all-NA in one of the frames out
    when it picks the dtype of that column in the result; this is deprecated
    (a ``FutureWarning``) and pandas 3 includes it. The qgeometry tables hit
    this all the time: ``fillet`` is an all-NA ``object`` column in the
    ``poly`` table and ``float64`` in ``path``, and a table starts empty.
    Here such columns are cast, before the concat, to the dtype of the frames
    that have values in that column, when that dtype can hold NA (pandas 2
    does not exclude them otherwise; nor does this). No frame or
    column is dropped, so the columns, their order, the index and the frame
    type are those of ``pd.concat``.

    Args:
        frames (list): DataFrames (or GeoDataFrames) to concatenate.
        **kwargs: Passed to ``pd.concat``.

    Returns:
        pd.DataFrame: The concatenated frame.
    """
    frames = list(frames)
    columns = {}
    for frame in frames:
        for col in frame.columns:
            columns.setdefault(col, None)
    for col in columns:
        with_values, without = [], []
        for i, frame in enumerate(frames):
            if col not in frame.columns:
                continue
            series = frame[col]
            if not isinstance(series, pd.Series):  # duplicated column name
                with_values, without = [], []
                break
            if len(series) and not series.isna().all():
                with_values.append(series)
            else:
                without.append(i)
        if not with_values or not without:
            continue
        dtypes = {str(series.dtype): series.dtype for series in with_values}
        if len(dtypes) == 1:
            target = next(iter(dtypes.values()))
        else:
            target = pd.concat(
                [series.iloc[:0] for series in with_values], ignore_index=True
            ).dtype
        for i in without:
            frame = frames[i]
            # pandas 2 fills the column with the NA of ``target`` only when
            # ``target`` has one; for int or bool it keeps the column as is,
            # e.g. an empty ``object`` column next to an int one gives object.
            if frame[col].dtype != target and _holds_na(target):
                frames[i] = frame.astype({col: target})
    return pd.concat(frames, **kwargs)
