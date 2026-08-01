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
"""Tests for :func:`qiskit_metal.view` — the headless matplotlib viewer.

The viewer is the no-Qt path for rendering designs (Jupyter, Binder,
Colab, scripts, CI). These tests pin both the API surface and
behavior expected by tutorials and downstream users.

The matplotlib backend is forced to ``Agg`` (non-interactive, no
display) before any matplotlib import so the suite works on headless
CI runners without an X server.
"""

import io
import unittest

import matplotlib

matplotlib.use("Agg")  # noqa: E402  must run before pyplot import below

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from qiskit_metal import Dict, designs, view
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.sample_shapes.rectangle import Rectangle
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.renderers.renderer_mpl.mpl_renderer import QMplRenderer


def _make_design_with_two_components():
    design = designs.DesignPlanar()
    TransmonPocket(design, "Q1", options=Dict(connection_pads=Dict(a=Dict())))
    OpenToGround(design, "G1")
    return design


def _render_to_png_bytes(fig) -> bytes:
    """Save ``fig`` to PNG bytes — used for comparing two renders for
    pixel-level inequality without caring about artist structure."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=60)
    return buf.getvalue()


class TestViewerStandalone(unittest.TestCase):
    """``qm.view(design)`` produces a valid matplotlib Figure with no
    Qt dependency. All tests run with the ``Agg`` backend — if any
    code path reaches for Qt at render time the test fails."""

    def tearDown(self):
        plt.close("all")

    def test_view_returns_figure_with_default_args(self):
        """The no-args call returns a Figure, not None / not an Axes."""
        design = _make_design_with_two_components()
        fig = view(design)
        self.assertIsInstance(fig, Figure)

    def test_view_into_existing_axes(self):
        """When ``ax`` is passed, the returned Figure is ``ax.figure``
        and no new figure is created."""
        design = _make_design_with_two_components()
        fig, ax = plt.subplots(figsize=(6, 6))
        n_before = len(plt.get_fignums())
        returned = view(design, ax=ax)
        n_after = len(plt.get_fignums())
        self.assertIs(returned, fig)
        self.assertEqual(n_before, n_after, "view(ax=...) must not create a new Figure")

    def test_view_respects_figsize(self):
        """The new Figure is created at the requested size."""
        design = _make_design_with_two_components()
        fig = view(design, figsize=(4.0, 3.0))
        self.assertAlmostEqual(fig.get_figwidth(), 4.0, places=3)
        self.assertAlmostEqual(fig.get_figheight(), 3.0, places=3)

    def test_view_empty_design_does_not_error(self):
        """Calling ``view`` on a design with zero components must not
        raise — a blank canvas is a valid result (matches what GUI
        users see when they start a new project)."""
        design = designs.DesignPlanar()
        fig = view(design)
        self.assertIsInstance(fig, Figure)

    def test_view_aspect_is_equal(self):
        """Designs must render with ``aspect=equal`` — otherwise pads
        and pockets look stretched and users misjudge geometry."""
        design = _make_design_with_two_components()
        fig = view(design)
        ax = fig.axes[0]
        # matplotlib returns 'equal' or a float for the data aspect.
        aspect = ax.get_aspect()
        self.assertTrue(
            aspect == "equal" or aspect == 1.0, f"Expected equal aspect, got {aspect!r}"
        )

    def test_view_filters_to_named_components(self):
        """``components=[name]`` must hide all components not in the
        list. We verify by comparing the *image bytes* of the
        filtered vs unfiltered render — they must differ. Counting
        matplotlib artists isn't a viable check because both
        renders use the same ``PatchCollection`` batching; a single
        ``PatchCollection`` may hold geometry from many components.
        """
        design = _make_design_with_two_components()
        # ``chip_outline=False`` so the view frames the geometry rather than
        # the whole die. With the die in frame these two components are a few
        # pixels apart at this figure size and the PNGs come out identical --
        # the test would pass or fail on rasterisation, not on filtering.
        png_all = _render_to_png_bytes(view(design, figsize=(4, 4), chip_outline=False))
        png_filtered = _render_to_png_bytes(
            view(design, components=["Q1"], figsize=(4, 4), chip_outline=False)
        )
        self.assertNotEqual(
            png_all,
            png_filtered,
            "Filtering to one component should produce a different "
            "image than rendering all components.",
        )

    def test_view_filters_with_unknown_component_name(self):
        """An unknown name in ``components`` shouldn't crash — it just
        produces an empty filter (everything hidden) which is still a
        valid empty render."""
        design = _make_design_with_two_components()
        fig = view(design, components=["does_not_exist"])
        self.assertIsInstance(fig, Figure)

    def test_view_hides_layers(self):
        """``hidden_layers={N}`` must suppress geometry on layer N.
        We verify by comparing image bytes of all-visible vs
        layer-hidden renders — they must differ when layer 1 (which
        contains every default-options component's geometry) is
        hidden.
        """
        design = _make_design_with_two_components()
        png_all = _render_to_png_bytes(view(design, figsize=(4, 4)))
        png_hidden = _render_to_png_bytes(
            view(design, hidden_layers={1}, figsize=(4, 4))
        )
        self.assertNotEqual(
            png_all,
            png_hidden,
            "Hiding layer 1 should produce a different image than "
            "rendering with all layers visible.",
        )

    def test_view_sets_title_when_given(self):
        design = _make_design_with_two_components()
        fig = view(design, title="My beautiful design")
        self.assertEqual(fig.axes[0].get_title(), "My beautiful design")

    def test_view_savefig_roundtrip(self):
        """Sanity check — the returned Figure can be saved to PNG bytes
        without error. This is the common Jupyter / CI artifact path."""
        design = _make_design_with_two_components()
        fig = view(design, figsize=(4, 4))
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=72)
        self.assertGreater(buf.tell(), 0)


class TestQMplRendererStandalone(unittest.TestCase):
    """``QMplRenderer(design)`` must work with no ``canvas`` arg."""

    def tearDown(self):
        plt.close("all")

    def test_constructs_without_canvas(self):
        """The standalone constructor must accept just ``design`` and
        not require a Qt PlotCanvas."""
        design = designs.DesignPlanar()
        renderer = QMplRenderer(design=design)
        self.assertIsNone(renderer.canvas)
        self.assertIs(renderer.design, design)

    def test_render_accepts_arbitrary_axes(self):
        """``render(ax)`` must accept any matplotlib Axes — not just
        one that came from a Qt canvas."""
        design = designs.DesignPlanar()
        Rectangle(design, "R1")
        renderer = QMplRenderer(design=design)
        fig, ax = plt.subplots()
        renderer.render(ax)  # must not raise

    def test_legacy_canvas_keyword_still_accepted(self):
        """The legacy Qt call site uses ``QMplRenderer(canvas=...,
        design=..., logger=...)``. Confirm that signature still works
        so we don't break ``mpl_canvas.PlotCanvas``."""
        # We pass a placeholder object — the renderer stores it on
        # self.canvas but never calls anything on it (verified by
        # grep). Using object() is safer than mocking PlotCanvas
        # (which would pull in PySide6 at test time).
        design = designs.DesignPlanar()
        sentinel = object()
        renderer = QMplRenderer(design=design, canvas=sentinel)
        self.assertIs(renderer.canvas, sentinel)


class TestViewBackendConditionalClose(unittest.TestCase):
    """Regression for the plt.close() on widget backend bug in view.py.

    With Agg/inline, the figure must be deregistered from pyplot after
    view() so it doesn't double-render in Jupyter.  With interactive
    backends (ipympl, Qt) plt.close() destroys the canvas — so view()
    must NOT close in those cases.  This file forces Agg at the module
    level, so only the Agg branch is exercised here.
    """

    def tearDown(self):
        plt.close("all")

    def test_agg_figure_not_in_pyplot_manager_after_view(self):
        """With Agg, view() must deregister the figure from pyplot so
        Jupyter's post_execute hook doesn't display it a second time."""
        design = _make_design_with_two_components()
        fig = view(design)
        self.assertNotIn(
            fig.number,
            plt.get_fignums(),
            "With Agg backend, view() must close the figure to prevent "
            "double-rendering in Jupyter (plt.close regression).",
        )

    def test_agg_returned_figure_is_still_usable(self):
        """Closing from pyplot must not corrupt the Figure object —
        savefig and axes access must still work after view() returns."""
        import io

        design = _make_design_with_two_components()
        fig = view(design)
        # axes still accessible
        self.assertEqual(len(fig.axes), 1)
        # savefig still works
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=60)
        self.assertGreater(buf.tell(), 0)


class TestAboutNoQt(unittest.TestCase):
    """``qm.about()`` must not require PySide6 — it's a debug helper
    that lite-mode users rely on. Lives in test_viewer.py because
    that file is in the tests-lite suite; test_toolbox_metal.py is
    not, so a regression there wouldn't be caught before users."""

    def test_about_runs_without_pyside6(self):
        """about() must return its summary string even when PySide6 /
        SIP aren't installed. In the lite CI venv this exercises the
        real ImportError branch; in the full venv it exercises the
        success path but still confirms about() doesn't raise."""
        from qiskit_metal.toolbox_metal import about as about_module

        text = about_module.about()
        self.assertIsInstance(text, str)
        # The summary always reports something for these fields,
        # even in lite mode where the value is "Not installed".
        self.assertIn("PySide6 version", text)
        self.assertIn("Qt version", text)
        self.assertIn("SIP version", text)


class TestChipOutline(unittest.TestCase):
    """The die extent is drawn, so geometry off the chip is visible.

    Every renderer downstream silently clips geometry outside the die.
    Without an outline on screen there is nothing that says a launchpad
    is hanging off the edge -- which is exactly how it shipped in two
    Appendix A reference designs.
    """

    def _outlines(self, ax):
        from matplotlib.patches import Rectangle as MplRectangle

        return [p for p in ax.patches if isinstance(p, MplRectangle)]

    def test_outline_drawn_by_default(self):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        design.chips.main.size.size_x = "6mm"
        design.chips.main.size.size_y = "4mm"
        TransmonPocket(design, "Q1")
        design.rebuild()

        fig, ax = plt.subplots()
        view(design, ax=ax)

        outlines = self._outlines(ax)
        self.assertEqual(len(outlines), 1, msg=f"got {outlines}")
        x, y = outlines[0].get_xy()
        self.assertAlmostEqual(x, -3.0, places=6)
        self.assertAlmostEqual(y, -2.0, places=6)
        self.assertAlmostEqual(outlines[0].get_width(), 6.0, places=6)
        self.assertAlmostEqual(outlines[0].get_height(), 4.0, places=6)
        plt.close(fig)

    def test_outline_can_be_turned_off(self):
        design = designs.DesignPlanar()
        TransmonPocket(design, "Q1")
        design.rebuild()

        fig, ax = plt.subplots()
        view(design, ax=ax, chip_outline=False)
        self.assertEqual(self._outlines(ax), [])
        plt.close(fig)

    def test_outline_expands_the_view_to_the_whole_die(self):
        """A single small component must not hide how big the die is."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        design.chips.main.size.size_x = "10mm"
        design.chips.main.size.size_y = "10mm"
        TransmonPocket(design, "Q1")
        design.rebuild()

        fig, ax = plt.subplots()
        view(design, ax=ax)
        xmin, xmax = ax.get_xlim()
        self.assertLessEqual(xmin, -5.0)
        self.assertGreaterEqual(xmax, 5.0)
        plt.close(fig)

    def test_off_chip_geometry_still_in_view(self):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        design.chips.main.size.size_x = "2mm"
        design.chips.main.size.size_y = "2mm"
        TransmonPocket(design, "Q_far", options=Dict(pos_x="4mm"))
        design.rebuild()

        fig, ax = plt.subplots()
        view(design, ax=ax)
        _, xmax = ax.get_xlim()
        # The outline ends at 1mm; the component is out at 4mm. Both are
        # on screen or the mismatch is invisible, which is the whole point.
        self.assertGreater(xmax, 3.5)
        self.assertEqual(len(self._outlines(ax)), 1)
        plt.close(fig)

    def test_every_chip_gets_an_outline(self):
        design = designs.DesignFlipChip()
        design.rebuild()

        fig, ax = plt.subplots()
        view(design, ax=ax)
        self.assertEqual(len(self._outlines(ax)), len(design.chips))
        labels = {t.get_text() for t in ax.texts}
        self.assertEqual(labels, set(design.chips.keys()))
        plt.close(fig)

    def test_chip_without_a_size_is_skipped_not_fatal(self):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        design.chips.main.pop("size")
        TransmonPocket(design, "Q1")
        design.rebuild()

        renderer = QMplRenderer(design=design)
        fig, ax = plt.subplots()
        renderer.render(ax)  # must not raise
        self.assertIsNone(renderer.chip_bounds("main"))
        self.assertEqual(self._outlines(ax), [])
        plt.close(fig)


if __name__ == "__main__":
    unittest.main(verbosity=2)
