# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""``QGDSRenderer.options.path_filename`` defaults to None (#1223).

The old default, ``"../resources/Fake_Junctions.GDS"``, resolved against the
working directory and pointed at a file that is not installed with the
package. ``None`` means "no junction cell replacement": the export says so
once and leaves junction geometry out, and ``None`` used to raise TypeError.
"""

import logging
import os
import tempfile
import unittest
from pathlib import Path

import gdstk

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer

FAKE_JUNCTIONS = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "tut"
    / "resources"
    / "Fake_Junctions.GDS"
)


def _flip_chip_with_two_junctions():
    design = designs.DesignFlipChip()
    TransmonPocket(design, "Q1", options=dict(chip="Q_chip"))
    TransmonPocket(design, "Q2", options=dict(chip="C_chip"))
    design.rebuild()
    gds = design.renderers.gds
    for chip in design.chips:
        gds.options.cheese.view_in_file[chip] = {1: False}
        gds.options.no_cheese.view_in_file[chip] = {1: False}
    return design, gds


def _warnings_about(records, text):
    return [
        r for r in records if r.levelno >= logging.WARNING and text in r.getMessage()
    ]


class TestJunctionFileDefault(unittest.TestCase):
    def test_default_is_none(self):
        self.assertIsNone(QGDSRenderer.default_options.path_filename)

    def test_no_file_exports_and_says_so_once_per_export(self):
        _, gds = _flip_chip_with_two_junctions()
        self.assertIsNone(gds.options.path_filename)
        out = os.path.join(tempfile.mkdtemp(), "a.gds")
        for _ in range(2):
            with self.assertLogs(gds.logger, level="WARNING") as caught:
                self.assertEqual(gds.export_to_gds(out), 1)
            notes = _warnings_about(caught.records, "no junction GDS file set")
            self.assertEqual(len(notes), 1, [r.getMessage() for r in caught.records])
            self.assertIn("gds.options.path_filename", notes[0].getMessage())

    def test_missing_file_warning_names_absolute_path(self):
        _, gds = _flip_chip_with_two_junctions()
        gds.options.path_filename = "no_such_dir/junctions.gds"
        out = os.path.join(tempfile.mkdtemp(), "a.gds")
        with self.assertLogs(gds.logger, level="WARNING") as caught:
            gds.export_to_gds(out)
        notes = _warnings_about(caught.records, "Not able to find file")
        self.assertTrue(notes)
        self.assertIn(
            os.path.abspath("no_such_dir/junctions.gds"), notes[0].getMessage()
        )

    @unittest.skipUnless(FAKE_JUNCTIONS.is_file(), "source checkout only")
    def test_explicit_file_places_junction_cell(self):
        _, gds = _flip_chip_with_two_junctions()
        gds.options.path_filename = str(FAKE_JUNCTIONS)
        out = os.path.join(tempfile.mkdtemp(), "a.gds")
        self.assertEqual(gds.export_to_gds(out), 1)
        names = {c.name for c in gdstk.read_gds(out).cells}
        self.assertIn("my_other_junction", names)


if __name__ == "__main__":
    unittest.main()
