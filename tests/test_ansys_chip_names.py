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
"""QAnsysRenderer finds a component's chip from its qgeometry (#1196).

``options.chip`` is only the default ``add_qgeometry`` and ``add_pin`` use; a
component can draw onto another chip explicitly. Runs without Ansys.
"""

import importlib.util
import unittest
from collections import defaultdict
from unittest.mock import MagicMock

import numpy as np

from qiskit_metal import designs, draw
from qiskit_metal.designs.design_flipchip import DesignFlipChip
from qiskit_metal.qlibrary.core import QComponent

HAS_PYEPR = importlib.util.find_spec("pyEPR") is not None


class PadOnChip(QComponent):
    """A pad and an open pin drawn on ``target_chip``; options.chip left at default."""

    default_options = dict(width="500um", height="500um", target_chip="Q_chip")

    def make(self):
        p = self.parse_options()
        pad = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        self.add_qgeometry("poly", {"pad": pad}, chip=p.target_chip)
        half = p.width / 2
        self.add_pin(
            "a",
            np.array([[half, -0.01], [half, 0.01]]),
            width=0.02,
            chip=p.target_chip,
        )


class NoGeometry(QComponent):
    """Draws nothing, so only options.chip says where it is."""

    def make(self):
        pass


def _renderer(design, selection=None):
    renderer = design.renderers.hfss
    renderer.qcomp_ids, renderer.case = renderer.get_unique_component_ids(selection)
    return renderer


@unittest.skipUnless(HAS_PYEPR, "QAnsysRenderer needs pyEPR")
class TestGetChipNames(unittest.TestCase):
    def test_chip_comes_from_geometry_not_options(self):
        """The #1196 reproducer: options.chip is 'main', which DesignFlipChip lacks."""
        design = DesignFlipChip({}, True)
        PadOnChip(design, "Q1")
        self.assertEqual(design.components["Q1"].options.chip, "main")
        self.assertEqual(_renderer(design).get_chip_names(), ["Q_chip"])

    def test_selection_only_reports_its_own_chips(self):
        design = DesignFlipChip({}, True)
        PadOnChip(design, "Q1")
        PadOnChip(design, "C1", options=dict(target_chip="C_chip", pos_x="2mm"))
        self.assertEqual(_renderer(design, ["C1"]).get_chip_names(), ["C_chip"])
        self.assertEqual(
            sorted(_renderer(design).get_chip_names()), ["C_chip", "Q_chip"]
        )

    def test_single_chip_design_unchanged(self):
        design = designs.DesignPlanar({}, True)
        PadOnChip(design, "Q1", options=dict(target_chip="main"))
        self.assertEqual(_renderer(design).get_chip_names(), ["main"])

    def test_component_without_geometry_falls_back_to_options_chip(self):
        design = designs.DesignPlanar({}, True)
        NoGeometry(design, "empty")
        self.assertEqual(_renderer(design).get_chip_names(), ["main"])


@unittest.skipUnless(HAS_PYEPR, "QAnsysRenderer needs pyEPR")
class TestAddEndcaps(unittest.TestCase):
    def test_endcap_uses_the_pins_chip(self):
        """Before #1196 the z came from options.chip: KeyError 'main' here."""
        design = DesignFlipChip({}, True)
        PadOnChip(design, "Q1")
        renderer = _renderer(design)
        renderer._pinfo = MagicMock()  # modeler is pinfo.design.modeler
        renderer.chip_subtract_dict = defaultdict(set)

        renderer.add_endcaps([("Q1", "a")])

        self.assertEqual(renderer.chip_subtract_dict["Q_chip"], {"endcap_Q1_a"})
        rect_mid = renderer.modeler.draw_rect_center.call_args.args[0]
        self.assertAlmostEqual(rect_mid[2], 20e-6)  # Q_chip center_z = 20 um, in metres


if __name__ == "__main__":
    unittest.main()
