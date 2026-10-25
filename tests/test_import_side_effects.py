# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Importing qiskit_metal must not change process-global state it does not own."""

import os
import subprocess
import sys
import textwrap
import unittest

_SCRIPT = textwrap.dedent(
    """
    import logging, warnings
    import qiskit_metal  # noqa: F401
    assert logging._warnings_showwarning is None, "captureWarnings was enabled"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warnings.warn("after import")
    assert [str(w.message) for w in caught] == ["after import"], caught
    print("OK")
    """
)


class TestImportSideEffects(unittest.TestCase):
    def test_import_does_not_capture_warnings(self):
        """#1229: ``import qiskit_metal`` used to call
        ``logging.captureWarnings(True)``, which silenced every later
        ``warnings.warn`` in the process. Run in a fresh interpreter so
        other tests' imports cannot mask the result."""
        env = dict(os.environ, QISKIT_METAL_HEADLESS="1")
        proc = subprocess.run(
            [sys.executable, "-c", _SCRIPT],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
