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


if __name__ == "__main__":
    unittest.main()
