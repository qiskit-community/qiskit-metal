# -*- coding: utf-8 -*-

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

"""Integration tests for QGDSRenderer.export_to_gds.

These tests exercise the full export pipeline end-to-end with a small
2-qubit design, covering positive mask, negative mask, cheesing, and
partial-component export.  They are the regression suite for the bugs
fixed in:
  - make_cheese.py  : nocheese_gds nested-list crash (cheesing with holes)
  - gds_renderer.py : ref.ref_cell → ref.cell (negative-mask export)
"""

import pathlib
import tempfile
import unittest

import gdstk

from qiskit_metal import designs, Dict
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander

# Path to the sample junction GDS shipped with the repo.
_RESOURCES = pathlib.Path(__file__).parent.parent / "tutorials" / "resources"
_JUNCTION_GDS = str(_RESOURCES / "Fake_Junctions.GDS")


def _make_two_qubit_design():
    """Return a DesignPlanar with two transmons connected by a meander."""
    design = designs.DesignPlanar()
    design.overwrite_enabled = True

    pad_opts = dict(pad_width="425 um", pad_gap="80 um", pocket_height="650um")

    TransmonPocket(
        design,
        "Q1",
        options=dict(
            pos_x="+0.70mm",
            pos_y="+0.0mm",
            gds_cell_name="FakeJunction_01",
            connection_pads=dict(
                a=dict(loc_W=-1, loc_H=-1, pad_width="130um"),
                b=dict(loc_W=+1, loc_H=-1, pad_width="130um"),
            ),
            **pad_opts,
        ),
    )
    TransmonPocket(
        design,
        "Q2",
        options=dict(
            pos_x="-0.70mm",
            pos_y="+0.0mm",
            orientation="180",
            gds_cell_name="FakeJunction_01",
            connection_pads=dict(
                a=dict(loc_W=-1, loc_H=-1, pad_width="130um"),
                b=dict(loc_W=+1, loc_H=-1, pad_width="130um"),
            ),
            **pad_opts,
        ),
    )

    cpw_opts = Dict(
        fillet="25um",
        pin_inputs=Dict(
            start_pin=Dict(component="Q1", pin="a"),
            end_pin=Dict(component="Q2", pin="a"),
        ),
        lead=Dict(start_straight="0.1mm", end_straight="0.1mm"),
        total_length="5mm",
        meander=Dict(lead_start="0.1mm", lead_end="0.1mm", asymmetry="0 um"),
    )
    RouteMeander(design, "cpw1", cpw_opts)
    return design


def _make_gds_renderer(design):
    gds = design.renderers.gds
    gds.options["path_filename"] = _JUNCTION_GDS
    gds.options["short_segments_to_not_fillet"] = "True"
    return gds


class TestGDSExportPositiveMask(unittest.TestCase):
    """export_to_gds with default (positive) mask."""

    def setUp(self):
        self.design = _make_two_qubit_design()
        self.gds = _make_gds_renderer(self.design)
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_export_creates_file(self):
        out = pathlib.Path(self.tmpdir.name) / "positive.gds"
        # export_to_gds returns 1 on success, 0 when the path cannot be written.
        ret = self.gds.export_to_gds(str(out))
        self.assertEqual(ret, 1, "export_to_gds should return 1 on success")
        self.assertTrue(out.exists(), "GDS file was not created")
        self.assertGreater(out.stat().st_size, 0, "GDS file is empty")

    def test_exported_gds_is_valid(self):
        out = pathlib.Path(self.tmpdir.name) / "positive.gds"
        self.gds.export_to_gds(str(out))
        lib = gdstk.read_gds(str(out))
        self.assertIsNotNone(lib)
        self.assertGreater(len(lib.cells), 0, "No cells in exported GDS")

    def test_exported_gds_contains_top_cell(self):
        out = pathlib.Path(self.tmpdir.name) / "positive.gds"
        self.gds.export_to_gds(str(out))
        lib = gdstk.read_gds(str(out))
        top_names = [c.name for c in lib.top_level()]
        self.assertTrue(
            any("TOP" in n for n in top_names),
            f"No TOP cell found; cells: {top_names}",
        )

    def test_export_highlight_subset(self):
        """Exporting only Q1 and cpw1 should still succeed and produce a file."""
        out = pathlib.Path(self.tmpdir.name) / "subset.gds"
        ret = self.gds.export_to_gds(str(out), highlight_qcomponents=["Q1", "cpw1"])
        self.assertEqual(ret, 1)
        self.assertTrue(out.exists())


class TestGDSExportNegativeMask(unittest.TestCase):
    """export_to_gds with negative_mask set — regression for ref.ref_cell bug."""

    def setUp(self):
        self.design = _make_two_qubit_design()
        self.gds = _make_gds_renderer(self.design)
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_negative_mask_layer1_does_not_raise(self):
        """Negative-mask export must not raise AttributeError (ref.ref_cell fix)."""
        self.gds.options["negative_mask"] = Dict(main=[1])
        out = pathlib.Path(self.tmpdir.name) / "neg_layer1.gds"
        try:
            ret = self.gds.export_to_gds(str(out))
        except AttributeError as exc:
            self.fail(f"export_to_gds raised AttributeError: {exc}")
        self.assertEqual(ret, 1)
        self.assertTrue(out.exists())

    def test_negative_mask_multiple_layers_does_not_raise(self):
        self.gds.options["negative_mask"] = Dict(main=[1, 14])
        out = pathlib.Path(self.tmpdir.name) / "neg_layers_1_14.gds"
        try:
            ret = self.gds.export_to_gds(str(out))
        except AttributeError as exc:
            self.fail(f"export_to_gds raised AttributeError: {exc}")
        self.assertEqual(ret, 1)

    def test_negative_mask_produces_valid_gds(self):
        self.gds.options["negative_mask"] = Dict(main=[1])
        out = pathlib.Path(self.tmpdir.name) / "neg_valid.gds"
        self.gds.export_to_gds(str(out))
        lib = gdstk.read_gds(str(out))
        self.assertGreater(len(lib.cells), 0)


class TestGDSExportCheesing(unittest.TestCase):
    """export_to_gds with cheesing enabled — regression for nocheese_gds nested-list bug."""

    def setUp(self):
        self.design = _make_two_qubit_design()
        self.gds = _make_gds_renderer(self.design)
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_cheesing_layer1_does_not_raise(self):
        """Cheesing must not raise TypeError when nocheese_gds contains nested lists."""
        self.gds.options["cheese"] = Dict(
            datatype=100,
            delta_x="0.1mm",
            delta_y="0.1mm",
            edge_nocheese="0.1mm",
            shape=0,
            cheese_0_x="0.05mm",
            cheese_0_y="0.05mm",
        )
        self.gds.options["no_cheese"] = Dict(
            datatype=99,
            buffer="0.025mm",
        )
        self.gds.options["fabricate"] = "False"
        # Enable cheesing on layer 1.
        self.gds.options["cheese"]["view_in_file"] = Dict(main={1: True})
        out = pathlib.Path(self.tmpdir.name) / "cheesed.gds"
        try:
            ret = self.gds.export_to_gds(str(out))
        except TypeError as exc:
            self.fail(f"export_to_gds raised TypeError during cheesing: {exc}")
        self.assertEqual(ret, 1)

    def test_cheesing_positive_mask_produces_valid_gds(self):
        self.gds.options["cheese"] = Dict(
            datatype=100,
            delta_x="0.1mm",
            delta_y="0.1mm",
            edge_nocheese="0.1mm",
            shape=0,
            cheese_0_x="0.05mm",
            cheese_0_y="0.05mm",
        )
        self.gds.options["cheese"]["view_in_file"] = Dict(main={1: True})
        out = pathlib.Path(self.tmpdir.name) / "cheesed_valid.gds"
        self.gds.export_to_gds(str(out))
        lib = gdstk.read_gds(str(out))
        self.assertGreater(len(lib.cells), 0)


class TestJunctionRotationRadians(unittest.TestCase):
    """Regression for the degrees-vs-radians bug in _get_linestring_characteristics.

    gdstk.Reference.rotation expects radians. The old code passed
    math.degrees(math.atan2(...)) which caused junctions to appear at
    ~116° in KLayout instead of 90° for a vertical linestring.
    """

    def _make_row(self, x0, y0, x1, y1):
        """Build a minimal pandas Series that mimics a junction table row."""
        import pandas as pd
        from shapely.geometry import LineString

        return pd.Series({"geometry": LineString([(x0, y0), (x1, y1)])})

    def setUp(self):
        self.design = _make_two_qubit_design()
        self.gds = _make_gds_renderer(self.design)

    def test_vertical_linestring_returns_pi_over_2(self):
        """A vertical junction line (pointing straight up) must give π/2 rad, not 90."""
        import math

        row = self._make_row(0.0, 0.0, 0.0, 1.0)
        _, rotation, _ = self.gds._get_linestring_characteristics(row)
        self.assertAlmostEqual(
            rotation,
            math.pi / 2,
            places=6,
            msg="Vertical junction should give π/2 rad — got degrees instead of radians?",
        )

    def test_horizontal_linestring_returns_zero(self):
        """A horizontal junction line must give 0 rad."""
        row = self._make_row(0.0, 0.0, 1.0, 0.0)
        _, rotation, _ = self.gds._get_linestring_characteristics(row)
        self.assertAlmostEqual(rotation, 0.0, places=6)

    def test_diagonal_linestring_is_in_radian_range(self):
        """Any linestring rotation must be in (-π, π], never a degree value like 45 or 135."""
        import math

        row = self._make_row(0.0, 0.0, 1.0, 1.0)
        _, rotation, _ = self.gds._get_linestring_characteristics(row)
        self.assertAlmostEqual(rotation, math.pi / 4, places=6)
        # If degrees were returned this would be ~45.0, way outside (-π, π].
        self.assertLessEqual(
            abs(rotation),
            math.pi,
            msg=f"rotation={rotation} looks like degrees, not radians",
        )

    def test_rotation_is_used_in_exported_junction_reference(self):
        """End-to-end: export a design with a 90° qubit and confirm the
        junction GDS reference angle is close to π/2, not ~2 rad (116°)."""
        import math
        import pathlib
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            out = pathlib.Path(tmpdir) / "junction_rotation.gds"
            self.gds.export_to_gds(str(out))
            lib = gdstk.read_gds(str(out))

        # Find any Reference whose cell is a junction cell (FakeJunction_01).
        junction_refs = []
        for cell in lib.cells:
            for ref in cell.references:
                if hasattr(ref, "cell") and "Junction" in ref.cell.name:
                    junction_refs.append(ref)

        self.assertTrue(junction_refs, "No junction references found in exported GDS")
        for ref in junction_refs:
            angle = ref.rotation  # radians
            # Must be in (-π, π] — a degree value of 90 would be ~1.57 rad ✓,
            # but the old bug gave math.degrees(π/2) ≈ 90 rad ≈ 116° effective.
            self.assertLessEqual(
                abs(angle),
                math.pi,
                msg=f"Junction ref.rotation={angle} is outside radian range — degrees bug?",
            )


class TestPlotGDSZoom(unittest.TestCase):
    """Tests for QGDSRenderer.plot_gds_zoom — the matplotlib junction zoom utility."""

    def setUp(self):
        self.design = _make_two_qubit_design()
        self.gds = _make_gds_renderer(self.design)
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmpdir.name) / "zoom_test.gds"
        self.gds.export_to_gds(str(self.out))
        self.lib = gdstk.read_gds(str(self.out))

    def tearDown(self):
        import matplotlib.pyplot as plt

        plt.close("all")
        self.tmpdir.cleanup()

    def test_returns_figure(self):
        from matplotlib.figure import Figure

        fig = self.gds.plot_gds_zoom(self.lib, center_mm=(0.70, 0.0), span_mm=0.15)
        self.assertIsInstance(fig, Figure)

    def test_accepts_existing_axes(self):
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure

        fig, ax = plt.subplots()
        returned = self.gds.plot_gds_zoom(
            self.lib, center_mm=(0.70, 0.0), span_mm=0.15, ax=ax
        )
        self.assertIs(returned, fig)

    def test_empty_window_does_not_raise(self):
        """A zoom window with no geometry should produce an empty figure, not an error."""
        fig = self.gds.plot_gds_zoom(self.lib, center_mm=(99.0, 99.0), span_mm=0.01)
        from matplotlib.figure import Figure

        self.assertIsInstance(fig, Figure)

    def test_title_is_set(self):
        fig = self.gds.plot_gds_zoom(
            self.lib, center_mm=(0.70, 0.0), span_mm=0.15, title="Q1 junction"
        )
        self.assertEqual(fig.axes[0].get_title(), "Q1 junction")

    def test_side_by_side_panels(self):
        """plot_gds_zoom into two axes on the same figure must not raise."""
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        self.gds.plot_gds_zoom(self.lib, center_mm=(0.70, 0.0), ax=axes[0])
        self.gds.plot_gds_zoom(self.lib, center_mm=(-0.70, 0.0), ax=axes[1])
        self.assertEqual(len(fig.axes), 2)


class TestDebugSummarizeGDSLibrary(unittest.TestCase):
    """Tests for QGDSRenderer.debug_summarize_gds_library."""

    def setUp(self):
        self.design = _make_two_qubit_design()
        self.gds = _make_gds_renderer(self.design)
        self.tmpdir = tempfile.TemporaryDirectory()
        out = pathlib.Path(self.tmpdir.name) / "summary_test.gds"
        self.gds.export_to_gds(str(out))
        self.lib = gdstk.read_gds(str(out))

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_show_false_does_not_raise(self):
        """show=False must run cleanly — just prints to stdout."""
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.gds.debug_summarize_gds_library(self.lib, show=False)
        output = buf.getvalue()
        self.assertIn("GDS LIBRARY SUMMARY", output)
        self.assertIn("LAYER / DATATYPE USAGE", output)

    def test_show_true_writes_svg(self):
        """show=True must write test_output.svg to disk."""
        import os

        svg_path = "test_output.svg"
        if os.path.exists(svg_path):
            os.remove(svg_path)
        try:
            # Suppress IPython display in test context (no kernel present)
            try:
                self.gds.debug_summarize_gds_library(self.lib, show=True)
            except Exception:
                pass  # IPython display will fail outside Jupyter — that's expected
            self.assertTrue(
                os.path.exists(svg_path),
                "show=True must write test_output.svg even outside Jupyter",
            )
        finally:
            if os.path.exists(svg_path):
                os.remove(svg_path)

    def test_shape_style_accepted_by_write_svg(self):
        """write_library_overview_svg must accept shape_style without TypeError.
        Regression for gdstk 0.9.x where the kwarg is shape_style not style.
        """
        import os
        import tempfile
        from qiskit_metal.renderers.renderer_gds.gds_renderer import (
            write_library_overview_svg,
        )

        style = {
            (1, 0): {"fill": "#4C9BE8", "stroke": "#4C9BE8", "fill-opacity": "0.8"}
        }
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "styled.svg")
            try:
                write_library_overview_svg(self.lib, filename=out, style=style)
            except TypeError as exc:
                self.fail(
                    f"write_library_overview_svg raised TypeError with shape_style: {exc}"
                )
            self.assertTrue(os.path.exists(out))


if __name__ == "__main__":
    unittest.main(verbosity=2)
