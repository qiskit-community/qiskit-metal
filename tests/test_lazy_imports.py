# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""``import qiskit_metal`` and building a design leave qutip and gdstk out of
``sys.modules``, so the lite install path can load where they have no wheel
(e.g. Pyodide). They load on first use."""

import subprocess
import sys
import textwrap
import unittest

SCRIPT = textwrap.dedent(
    """
    import os, sys
    os.environ["QISKIT_METAL_HEADLESS"] = "1"

    class BlockOptional:
        # Lite install: pyEPR (an [ansys] extra) pulls qutip in on its own.
        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] == "pyEPR":
                raise ImportError(name)

    sys.meta_path.insert(0, BlockOptional())
    import qiskit_metal
    from qiskit_metal import designs
    from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
    design = designs.DesignPlanar()
    TransmonPocket(design, "Q1")
    leaked = [m for m in ("gdstk", "qutip") if m in sys.modules]
    print("LEAKED", leaked)
    # first use loads gdstk
    lib = design.renderers.gds.lib
    print("LOADED", "gdstk" in sys.modules, type(lib).__name__)
    """
)


class TestLazyImports(unittest.TestCase):
    def test_design_building_does_not_import_compiled_packages(self):
        out = subprocess.run(
            [sys.executable, "-c", SCRIPT], capture_output=True, text=True, timeout=300
        )
        self.assertEqual(out.returncode, 0, out.stderr[-2000:])
        self.assertIn("LEAKED []", out.stdout)
        self.assertIn("LOADED True Library", out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
