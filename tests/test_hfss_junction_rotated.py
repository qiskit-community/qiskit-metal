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
"""The legacy HFSS renderer puts a junction's RLC boundary or lumped port on
the junction's own line at any angle (issue #1242).

Only the Ansys COM layer is stubbed; pyEPR's ``draw_rect_corner`` and
``Rect.make_rlc_boundary`` run unchanged for the axis-aligned path. This
checks the geometry handed to Ansys, not the result in Ansys.
"""

import unittest
from types import SimpleNamespace

import numpy as np

try:
    from pyEPR.ansys import HfssModeler
except Exception:  # pragma: no cover - pyEPR is an optional extra
    HfssModeler = None

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


class FakeModeler:
    """Records the terminal line of the RLC boundary or lumped port."""

    _modeler = SimpleNamespace(CreateRectangle=lambda *a: "JJ_rect")
    _attributes_array = lambda self, **kw: []  # noqa: E731
    eval_expr = lambda self, x: float(x)  # noqa: E731
    rename_obj = lambda self, obj, name: obj  # noqa: E731

    def __init__(self):
        self.terminal_line = None
        self.sheets = []

    def draw_rect_corner(self, *args, **kwargs):
        return HfssModeler.draw_rect_corner(self, *args, **kwargs)

    def draw_polyline(self, pts, closed, **kw):
        if closed:
            self.sheets.append(np.array(pts))
        return SimpleNamespace(rename=lambda n: SimpleNamespace())

    def _make_lumped_rlc(self, r, l, c, start, end, obj_arr, name):
        self.terminal_line = (start, end)

    def _make_lumped_port(self, start, end, obj_arr, z0="50ohm", name="LumpPort"):
        self.terminal_line = (start, end)


@unittest.skipIf(HfssModeler is None, "pyEPR is not installed")
class TestHfssJunctionAtAnyAngle(unittest.TestCase):
    def render(self, orientation, as_port=False):
        design = designs.DesignPlanar({}, True)
        TransmonPocket(design, "Q1", options=dict(orientation=orientation))
        jj = design.qgeometry.tables["junction"].iloc[0]
        renderer = design.renderers.hfss
        modeler = FakeModeler()
        renderer._pinfo = SimpleNamespace(design=SimpleNamespace(modeler=modeler))
        renderer.jj_to_ignore, renderer.jj_lumped_ports, renderer.assign_mesh = (
            set(),
            {("Q1", "rect_jj"): (50, False)} if as_port else {},
            [],
        )
        renderer.render_element_junction(jj)
        coords = np.asarray(jj.geometry.coords) * 1e3  # mm -> um
        start, end = (np.asarray(p)[:2] * 1e6 for p in modeler.terminal_line)
        return coords, start, end, modeler

    def test_terminal_line_is_the_junction_line(self):
        for as_port in (False, True):
            for orientation in (0, 90, 30, 45, 135, 200):
                with self.subTest(orientation=orientation, as_port=as_port):
                    coords, start, end, _ = self.render(orientation, as_port)
                    forward = np.allclose(start, coords[0]) and np.allclose(
                        end, coords[1]
                    )
                    backward = np.allclose(start, coords[1]) and np.allclose(
                        end, coords[0]
                    )
                    self.assertTrue(forward or backward, (coords, start, end))

    def test_rotated_sheet_is_centred_on_the_junction(self):
        for orientation in (30, 45):
            with self.subTest(orientation=orientation):
                coords, _, _, modeler = self.render(orientation)
                self.assertEqual(len(modeler.sheets), 1)
                sheet = modeler.sheets[0][:, :2] * 1e6
                np.testing.assert_allclose(
                    sheet.mean(axis=0), coords.mean(axis=0), atol=1e-6
                )

    def test_axis_aligned_junctions_keep_the_rectangle_path(self):
        for orientation in (0, 90):
            with self.subTest(orientation=orientation):
                self.assertEqual(self.render(orientation)[3].sheets, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
