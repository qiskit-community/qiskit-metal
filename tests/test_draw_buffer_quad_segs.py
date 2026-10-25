"""``draw.buffer`` must not pass shapely's deprecated ``resolution=`` (#1228).

Shapely 2.1 deprecates ``resolution`` in favour of ``quad_segs`` (accepted
since 2.0, the package minimum). Every component that goes through
``draw.buffer`` used to emit a DeprecationWarning, and failed outright under
``-W error::DeprecationWarning``.
"""

import unittest
import warnings

from shapely.geometry import JOIN_STYLE

from qiskit_metal import designs, draw
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


class TestDrawBufferQuadSegs(unittest.TestCase):
    def test_buffer_emits_no_deprecation_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            out = draw.buffer(
                draw.rectangle(1, 1), 0.5, resolution=4, join_style=JOIN_STYLE.round
            )
        # resolution still sets the segments per quarter circle
        expected = draw.rectangle(1, 1).buffer(
            0.5, quad_segs=4, join_style=JOIN_STYLE.round
        )
        self.assertEqual(len(out.exterior.coords), len(expected.exterior.coords))
        self.assertAlmostEqual(out.area, expected.area)

    def test_transmon_pocket_with_pad_builds_under_error_filter(self):
        design = designs.DesignPlanar()
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            TransmonPocket(
                design,
                "Q1",
                options=dict(connection_pads=dict(a=dict(loc_W=1, loc_H=1))),
            )
        self.assertIn("a", design.components["Q1"].pins)


if __name__ == "__main__":
    unittest.main()
