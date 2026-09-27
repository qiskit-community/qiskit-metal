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
"""Gmsh path renderer: short (sub-width) lead segments (#1144).

A route's short pin stubs (e.g. a 5um segment on a 10um trace) collapse the
width-offset geometry and made Gmsh reject a zero-length line. The
``remove_degenerate_segments`` cleanup fixes it; endpoints are preserved."""

import unittest

from qiskit_metal.renderers.renderer_gmsh.gmsh_utils import remove_degenerate_segments


class TestRemoveDegenerateSegments(unittest.TestCase):
    """Pure-Python coverage (no gmsh needed)."""

    def test_drops_short_lead_and_trailing_stubs(self):
        # 5-unit stubs at both ends of a 10-unit-wide conductor.
        coords = [(0.0, 0.0), (0.005, 0.0), (1.0, 0.0), (1.0, 1.0), (1.0, 1.005)]
        out = remove_degenerate_segments(coords, min_len=0.01)
        # endpoints preserved
        self.assertEqual(out[0], (0.0, 0.0))
        self.assertEqual(out[-1], (1.0, 1.005))
        # the two sub-min_len stub vertices are gone
        self.assertNotIn((0.005, 0.0), out)
        self.assertEqual(len(out), 3)

    def test_noop_when_all_segments_long_enough(self):
        coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
        out = remove_degenerate_segments(coords, min_len=0.01)
        self.assertEqual([tuple(p) for p in out], coords)

    def test_preserves_final_endpoint_even_if_last_segment_short(self):
        # last real vertex sits within min_len of the endpoint -> drop the
        # interior vertex, never the endpoint.
        coords = [(0.0, 0.0), (1.0, 0.0), (1.001, 0.0)]
        out = remove_degenerate_segments(coords, min_len=0.01)
        self.assertEqual(out[0], (0.0, 0.0))
        self.assertEqual(out[-1], (1.001, 0.0))
        self.assertEqual(len(out), 2)

    def test_degenerate_inputs(self):
        self.assertEqual(remove_degenerate_segments([(0, 0)], 0.01), [(0, 0)])
        self.assertEqual(
            remove_degenerate_segments([(0, 0), (1, 0)], 0.0), [(0, 0), (1, 0)]
        )


def _gmsh_importable():
    try:
        import gmsh  # noqa: F401

        return True
    except Exception:
        return False


@unittest.skipUnless(
    _gmsh_importable(), "gmsh not installed (optional [mesh] extra); 3D render check"
)
class TestMeanderRendersIn3D(unittest.TestCase):
    """A RouteMeander adds short pin stubs; before #1144 it crashed the gmsh
    path renderer with 'Could not create line'. Skipped in the lite CI."""

    def test_meander_with_short_stubs_renders(self):
        import gmsh
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal import Dict
        from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
        from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        design = MultiPlanar()
        design.overwrite_enabled = True
        OpenToGround(design, "A", options=dict(pos_x="-0.6mm", orientation="0"))
        OpenToGround(design, "B", options=dict(pos_x="0.6mm", orientation="180"))
        RouteMeander(
            design,
            "cpw",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component="A", pin="open"),
                    end_pin=Dict(component="B", pin="open"),
                ),
                total_length="4mm",
                fillet="90um",
                trace_width="10um",
                trace_gap="6um",
                meander=Dict(spacing="0.3mm"),
            ),
        )
        design.rebuild()

        r = QGmshRenderer(design, layer_types=dict(metal=[1], dielectric=[3]))
        try:
            r.render_design(
                draw_sample_holder=False, mesh_geoms=False, box_plus_buffer=False
            )
            n_volumes = len(gmsh.model.getEntities(3))
        finally:
            r.close()
        self.assertGreater(n_volumes, 0)


@unittest.skipUnless(
    _gmsh_importable(), "gmsh not installed (optional [mesh] extra); 3D render check"
)
class TestNearlyStraightCornersRender(unittest.TestCase):
    """A filleted path through vertices that are straight to within rounding.

    The path angle came from ``arccos`` of a dot product that can round past
    1 (NaN), and a corner bent by ~1e-6 rad got a fillet arc shorter than the
    1e-9 rounding of its control points: gmsh raised 'Could not create circle
    arc'. Resampled traced lines hit both."""

    def test_renders(self):
        import gmsh
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal.qlibrary.tlines.polyline_cpw import PolylineCPW
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        design = MultiPlanar()
        design.overwrite_enabled = True
        # A coupler from a traced 17-qubit layout that raised the error.
        points = [
            [0.161803399, -0.11755705],
            [0.194164079, -0.14106846],
            [0.241930934, -0.158747972],
            [0.286256414, -0.154886508],
            [0.325959737, -0.132643281],
            [0.365663059, -0.110400055],
            [0.405366382, -0.088156829],
            [0.445069705, -0.065913603],
            [0.484773027, -0.043670376],
            [0.524835328, -0.022130627],
            [0.566964968, -0.005700654],
            [0.612005778, -1.9098e-05],
            [0.657515208, -0.000101048],
            [0.703024639, -0.000182998],
            [0.748534069, -0.000264947],
            [0.794043499, -0.000346897],
            [0.839552929, -0.000428847],
            [0.885062359, -0.000510797],
            [0.930571789, -0.000592746],
            [0.976081219, -0.000674696],
            [1.021590649, -0.000756646],
            [1.06710008, -0.000838596],
            [1.111077626, -0.006610503],
            [1.146043598, -0.033885422],
            [1.173559371, -0.06889895],
            [1.212673657, -0.079345757],
            [1.248117682, -0.052990504],
            [1.277879991, -0.019455952],
            [1.318218464, -0.002611507],
            [1.3692, 0.0],
            [1.4092, 0.0],
        ]
        PolylineCPW(
            design,
            "line",
            options=dict(points=points, fillet="15um", min_segment="30um"),
        )

        r = QGmshRenderer(design, layer_types=dict(metal=[1], dielectric=[3]))
        try:
            r.render_design(
                draw_sample_holder=False, mesh_geoms=False, box_plus_buffer=False
            )
            n_volumes = len(gmsh.model.getEntities(3))
        finally:
            r.close()
        self.assertGreater(n_volumes, 0)


if __name__ == "__main__":
    unittest.main()
