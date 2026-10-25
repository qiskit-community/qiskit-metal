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
"""Default level of the ``metal`` logger and the skipped-renderer messages
(#1229, second part)."""

import logging
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

from qiskit_metal import Dict, config, designs
from qiskit_metal.analyses.simulation import EigenmodeSim

_BROKEN = "broken_renderer"


class TestMetalLoggerLevel(unittest.TestCase):
    def test_info_after_import(self):
        # In a fresh interpreter: other tests may change the level.
        out = subprocess.run(
            [
                sys.executable,
                "-c",
                "import logging, qiskit_metal; print(logging.getLogger('metal').level)",
            ],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "QISKIT_METAL_HEADLESS": "1"},
        )
        self.assertEqual(int(out.stdout.strip().splitlines()[-1]), logging.INFO)


class TestSkippedRenderer(unittest.TestCase):
    """A renderer whose optional dependency is missing is skipped quietly, but
    the reason stays available."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with open(os.path.join(tmp.name, f"{_BROKEN}_mod.py"), "w") as f:
            f.write("raise ImportError('optional package xyz is not installed')\n")
        sys.path.insert(0, tmp.name)
        self.addCleanup(sys.path.remove, tmp.name)
        self.addCleanup(sys.modules.pop, f"{_BROKEN}_mod", None)
        renderers = Dict(config.renderers_to_load)
        renderers[_BROKEN] = Dict(path_name=f"{_BROKEN}_mod", class_name="Renderer")
        patcher = unittest.mock.patch.object(config, "renderers_to_load", renderers)
        patcher.start()
        self.addCleanup(patcher.stop)
        logger = logging.getLogger("metal")
        level = logger.level
        self.addCleanup(logger.setLevel, level)
        logger.setLevel(logging.INFO)

    def test_not_logged_at_info(self):
        with self.assertNoLogs("metal", level="INFO"):
            designs.DesignPlanar()

    def test_logged_at_debug(self):
        logging.getLogger("metal").setLevel(logging.DEBUG)
        with self.assertLogs("metal", level="DEBUG") as cm:
            designs.DesignPlanar()
        msgs = [r.getMessage() for r in cm.records if _BROKEN in r.getMessage()]
        self.assertEqual(len(msgs), 1)
        self.assertIn("skipped", msgs[0])
        self.assertEqual(
            [r.levelno for r in cm.records if _BROKEN in r.getMessage()],
            [logging.DEBUG],
        )

    def test_reason_is_recorded(self):
        design = designs.DesignPlanar()
        self.assertNotIn(_BROKEN, design.renderers)
        self.assertIn("xyz is not installed", design.skipped_renderers[_BROKEN])
        self.assertNotIn("gds", design.skipped_renderers)

    def test_analysis_error_gives_the_reason(self):
        design = designs.DesignPlanar()
        with self.assertRaises(ValueError) as cm:
            EigenmodeSim(design, _BROKEN)
        msg = str(cm.exception)
        self.assertIn("not started for this design", msg)
        self.assertIn("xyz is not installed", msg)


if __name__ == "__main__":
    unittest.main()
