# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Concatenating qgeometry tables raises no pandas FutureWarning and gives the
pandas 2 dtypes on pandas 2 and 3 ("concatenation with empty or all-NA
entries is deprecated")."""

import os
import tempfile
import unittest
import warnings

import numpy as np
import pandas as pd

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.toolbox_python.utility_functions import concat_tables


def _metal_future_warnings(caught):
    """FutureWarnings attributed to a qiskit_metal source file."""
    return [
        f"{w.filename}:{w.lineno}: {w.message}"
        for w in caught
        if issubclass(w.category, FutureWarning)
        and f"{os.sep}qiskit_metal{os.sep}" in w.filename
    ]


class TestConcatTables(unittest.TestCase):
    def concat(self, frames):
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            return concat_tables(frames, ignore_index=True)

    def test_all_na_object_column_takes_the_float_dtype(self):
        a = pd.DataFrame({"x": [1.0, 2.0], "f": pd.Series([None, None], dtype=object)})
        b = pd.DataFrame({"x": [3.0], "f": [0.5]})
        for frames in ([a, b], [b, a]):
            r = self.concat(frames)
            self.assertEqual(r["f"].dtype, np.float64)
            self.assertEqual(list(r.columns), list(frames[0].columns))
        self.assertTrue(np.isnan(self.concat([a, b])["f"][:2]).all())

    def test_empty_frame(self):
        e = pd.DataFrame(
            {"x": pd.Series([], dtype=float), "f": pd.Series([], dtype=object)}
        )
        r = self.concat([e, pd.DataFrame({"x": [3.0], "f": [0.5]})])
        self.assertEqual(r["f"].dtype, np.float64)
        # pandas 2 keeps object next to an int column (no NA for int)
        r = self.concat([e, pd.DataFrame({"x": [3.0], "f": [5]})])
        self.assertEqual(r["f"].dtype, object)
        self.assertEqual(r["f"].tolist(), [5])

    def test_all_na_next_to_int_or_bool_stays_object(self):
        a = pd.DataFrame({"f": pd.Series([None], dtype=object)})
        for value in (5, True):
            with self.subTest(value=value):
                r = self.concat([a, pd.DataFrame({"f": [value]})])
                self.assertEqual(r["f"].dtype, object)
                self.assertEqual(r["f"].tolist(), [None, value])

    def test_all_na_next_to_strings(self):
        # object on pandas 2, the str dtype on pandas 3
        a = pd.DataFrame({"f": pd.Series([None], dtype=object)})
        b = pd.DataFrame({"f": ["s"]})
        r = self.concat([a, b])
        self.assertEqual(r["f"].dtype, b["f"].dtype)
        self.assertTrue(pd.isna(r["f"][0]))
        self.assertEqual(r["f"][1], "s")

    def test_inputs_not_modified(self):
        a = pd.DataFrame({"f": pd.Series([None], dtype=object)})
        self.concat([a, pd.DataFrame({"f": [0.5]})])
        self.assertEqual(a["f"].dtype, object)


class TestNoPandasFutureWarning(unittest.TestCase):
    def test_build_and_export_gds(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            design = designs.DesignPlanar()
            design.overwrite_enabled = True
            pads = dict(
                connection_pads=dict(a=dict(loc_W=+1, loc_H=+1), b=dict(loc_W=-1))
            )
            TransmonPocket(design, "Q1", options=dict(pos_x="-1mm", **pads))
            TransmonPocket(
                design, "Q2", options=dict(pos_x="1mm", orientation="180", **pads)
            )
            RouteMeander(
                design,
                "bus",
                options=Dict(
                    total_length="4mm",
                    fillet="90um",
                    pin_inputs=Dict(
                        start_pin=Dict(component="Q1", pin="a"),
                        end_pin=Dict(component="Q2", pin="a"),
                    ),
                ),
            )
            OpenToGround(design, "open", options=dict(pos_x="1.5mm", pos_y="1mm"))
            design.rebuild()
            gds = design.renderers.gds
            gds.options.path_filename = None
            gds.options.cheese.view_in_file = Dict(main={1: True})
            gds.options.no_cheese.view_in_file = Dict(main={1: True})
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(gds.export_to_gds(os.path.join(tmp, "chip.gds")), 1)
        self.assertEqual(_metal_future_warnings(caught), [])


if __name__ == "__main__":
    unittest.main()
