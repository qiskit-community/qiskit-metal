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
"""QAnsysRenderer.epr_start junction bookkeeping (#1194).

Runs without Ansys: a pyEPR ``ProjectInfo`` built with ``do_connect=False``,
with the two methods that query Ansys for names stubbed out.
"""

import gc
import importlib.util
import unittest
from unittest.mock import patch

from qiskit_metal import designs

HAS_PYEPR = importlib.util.find_spec("pyEPR") is not None


def _junction(lj, cj, rect, line):
    return {"Lj_variable": lj, "Cj_variable": cj, "rect": rect, "line": line}


@unittest.skipUnless(HAS_PYEPR, "pyEPR not installed")
class TestEprStartJunctions(unittest.TestCase):
    def setUp(self):
        from pyEPR.project_info import ProjectInfo

        from qiskit_metal.renderers.renderer_ansys import ansys_renderer

        self.renderer = designs.DesignPlanar().renderers.hfss
        self.renderer._pinfo = ProjectInfo(do_connect=False)
        # ProjectInfo.__del__ logs; let it run while pytest's streams are open
        self.addCleanup(gc.collect)
        self.addCleanup(setattr, self.renderer, "_pinfo", None)
        patcher = patch.object(
            ansys_renderer.epr, "DistributedAnalysis", lambda pinfo: object()
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _ansys_names(self, variables, objects):
        self.renderer.pinfo.get_all_variables_names = lambda: variables
        self.renderer.pinfo.get_all_object_names = lambda: objects

    def _start_single_qubit(self):
        self._ansys_names(["Lj", "Cj"], ["rect_q1", "line_q1"])
        self.renderer.epr_start(
            junctions={"jj": _junction("Lj", "Cj", "rect_q1", "line_q1")}
        )

    def test_new_junction_set_replaces_previous(self):
        """Junctions of an earlier analysis must not reach validation."""
        self._start_single_qubit()
        self._ansys_names(
            ["Lj1", "Cj1", "Lj2", "Cj2"],
            ["rect_q1", "line_q1", "rect_q2", "line_q2"],
        )
        self.renderer.epr_start(
            junctions={
                "jj1": _junction("Lj1", "Cj1", "rect_q1", "line_q1"),
                "jj2": _junction("Lj2", "Cj2", "rect_q2", "line_q2"),
            }
        )
        self.assertEqual(sorted(self.renderer.pinfo.junctions), ["jj1", "jj2"])

    def test_empty_junctions_clears(self):
        """run_epr(no_junctions=True) passes {}: no junction may remain."""
        self._start_single_qubit()
        self.renderer.epr_start(junctions={})
        self.assertEqual(dict(self.renderer.pinfo.junctions), {})

    def test_none_keeps_junctions(self):
        """epr_get_stored_energy() and friends call epr_start() with None."""
        self._start_single_qubit()
        self.renderer.epr_start()
        self.assertEqual(list(self.renderer.pinfo.junctions), ["jj"])


if __name__ == "__main__":
    unittest.main()
