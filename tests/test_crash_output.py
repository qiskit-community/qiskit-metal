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

"""crash_excerpt keeps the crash location from a faulthandler dump."""

import subprocess
import sys
import textwrap
import unittest

from ._crash_output import crash_excerpt


class TestCrashExcerpt(unittest.TestCase):
    def test_real_segfault_keeps_the_stack(self):
        # Import numpy so faulthandler appends its long module list.
        code = textwrap.dedent(
            """
            import ctypes, numpy

            def crash_here():
                ctypes.string_at(0)

            crash_here()
            """
        )
        proc = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertNotEqual(proc.returncode, 0)
        excerpt = crash_excerpt(proc.stderr)
        self.assertRegex(excerpt, r"(?m)^(Fatal Python error|Windows fatal exception)")
        self.assertIn("crash_here", excerpt)
        self.assertNotIn("Extension modules:", excerpt)

    def test_extension_list_does_not_hide_the_stack(self):
        stderr = (
            "Fatal Python error: Segmentation fault\n\n"
            "Current thread 0x1 (most recent call first):\n"
            '  File "gui.py", line 42 in show\n\n'
            "Extension modules: " + ", ".join(f"mod{i}" for i in range(2000))
        )
        excerpt = crash_excerpt(stderr)
        self.assertIn('File "gui.py", line 42 in show', excerpt)
        self.assertNotIn("mod1999", excerpt)

    def test_keeps_the_message_printed_before_the_crash(self):
        stderr = (
            "qt.qpa.plugin: Could not load the Qt platform plugin 'xcb'\n"
            "Fatal Python error: Aborted\n\n"
            "Current thread 0x1 (most recent call first):\n"
            '  File "main_window_base.py", line 927 in kick_start_qApp\n'
        )
        excerpt = crash_excerpt(stderr)
        self.assertTrue(excerpt.startswith("qt.qpa.plugin"))
        self.assertIn("kick_start_qApp", excerpt)

    def test_no_crash_header_returns_tail(self):
        self.assertEqual(crash_excerpt("x" * 10 + "end", limit=3), "end")

    def test_empty(self):
        self.assertEqual(crash_excerpt(""), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
