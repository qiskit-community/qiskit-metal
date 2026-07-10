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

"""On-screen MetalGUI initialization regression (issues #1048 / #1109).

Distinct from ``test_gui_teardown.py`` (which only covers the exit-time
segfault that PR #1104 / v0.7.4 fixed). This test guards the *init* path:
multiple reporters on Windows 11 (and at least one on macOS) see
``MetalGUI(design)`` render the QMainWindow briefly as bare scaffolding
("variable table / object inspector" per #1109), then either silently
abandon the GUI or take the kernel down — no Python traceback either way.

The MARKER_INIT_OK assertion catches the silent-abandonment case;
non-zero return code catches the segfault case. Combined, they fail
loudly on either failure mode.

``restore_window_settings`` (issue #1048, PR #1122 / #1128) has four
layered defenses against persisted-state corruption, checked in this
order:

    1. ``QISKIT_METAL_RESET_UI_SETTINGS=1`` escape hatch
    2. ``metal_version`` mismatch  -> clear
    3. ``qt_version`` mismatch     -> clear
    4. ``display_fingerprint`` mismatch -> clear
    5. ``restore_in_progress`` cookie left set -> clear (crashed restore)
    6. otherwise: attempt the real restore, clearing on exception

Tests 3-5 below each tamper with exactly ONE field via direct QSettings
access (bypassing Qt) while leaving the earlier-checked fields matching
the real environment, so each test exercises the SPECIFIC branch named
in its title rather than falling through the version check at the top
(which would happen if a test just used a fully-synthetic settings
blob). Each test then re-reads the on-disk settings directly to confirm
the correct ``clear()`` actually fired, rather than only checking "the
subprocess didn't crash" (which could pass for the wrong reason).

Skips when PySide6 is absent (lite install) or when no display is
available (a desktop session on Windows/macOS, ``$DISPLAY`` or
``$WAYLAND_DISPLAY`` on Linux).
"""

import os
import subprocess
import sys
import unittest

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings  # noqa: E402


def _display_available() -> bool:
    """True when a usable display is reachable from this process.

    GHA windows-2025 / macos-15 runners and any normal desktop session
    always have a usable display. Linux needs ``$DISPLAY`` (X11) or
    ``$WAYLAND_DISPLAY`` (Wayland) -- or ``xvfb-run`` wrapping the
    invocation.
    """
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _settings() -> QSettings:
    """Direct handle to the same on-disk store MetalGUI subprocesses
    read/write (registry on Windows, plist on macOS, ini on Linux).
    Used by the test process to seed/tamper/verify state without going
    through a Qt event loop of its own."""
    return QSettings("QiskitMetal", "MainWindow")


def _clear_persisted_settings() -> None:
    s = _settings()
    s.clear()
    s.sync()


def _read_persisted_settings() -> dict:
    s = _settings()
    s.sync()  # force a fresh read from disk, not this process's cache
    return {
        "metal_version": s.value("metal_version", ""),
        "qt_version": s.value("qt_version", ""),
        "display_fingerprint": s.value("display_fingerprint", ""),
        "restore_in_progress": s.value("restore_in_progress", False, type=bool),
        "geometry": s.value("geometry", b"", type=bytes),
    }


# Minimal init reproducer from the issue.  Prints MARKER_INIT_OK only if
# MetalGUI.__init__ actually returned; immediate sys.exit(0) keeps the
# subprocess scope to "init only" (teardown is test_gui_teardown.py's job).
# Clears any pre-existing MetalGUI QSettings first so this test can't be
# poisoned by state left behind by an interactive dev run on the same
# account.
_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from PySide6.QtCore import QSettings\n"
    "QSettings('QiskitMetal', 'MainWindow').clear()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "print('MARKER_INIT_OK', flush=True)\n"
    "sys.exit(0)\n"
)

# Builds MetalGUI and explicitly saves window state (geometry, dock
# layout, metal_version, qt_version, display_fingerprint) -- the exact
# call a Jupyter kernel makes when the user closes the GUI. Does NOT
# clear settings first, since the whole point is to capture the real
# environment's version/qt/fingerprint values for the tamper-one-field
# tests below to build on.
_SAVE_STATE_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "gui.main_window.save_window_settings()\n"
    "print('MARKER_SAVED_STATE', flush=True)\n"
    "sys.exit(0)\n"
)

# Builds MetalGUI against whatever is currently persisted, without any
# setup or teardown of its own. Used as the "restore" half of every
# two-process test below.
_RESTORE_ONLY_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "print('MARKER_RESTORED_OK', flush=True)\n"
    "sys.exit(0)\n"
)


class TestGUIInitOnScreen(unittest.TestCase):
    """Issues #1048 / #1109 — MetalGUI.__init__ must complete without
    hanging or crashing on a real display, and must not silently brick
    itself (or an unrelated later launch) on stale persisted state."""

    def _run_snippet(
        self, snippet: str, marker: str, require_success: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute ``snippet`` in a fresh Python process under
        faulthandler. When ``require_success`` (default), assert it
        printed ``marker`` and exited cleanly; otherwise just return the
        completed process so the caller can inspect it (used for the
        "this launch may legitimately crash" half of the self-heal
        test)."""
        proc = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", snippet],
            capture_output=True,
            text=True,
            timeout=240,
        )
        if not require_success:
            return proc

        self.assertIn(
            marker,
            proc.stdout,
            msg=(
                f"MetalGUI.__init__ did not reach {marker} "
                "(wedged or silently abandoned -- issue #1109 / #1048).\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr tail:\n{proc.stderr[-2000:]}"
            ),
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=(
                f"MetalGUI init subprocess exited {proc.returncode} "
                "(non-zero / segfault -- issue #1048).\n"
                f"stderr tail:\n{proc.stderr[-2000:]}"
            ),
        )
        return proc

    def test_metalgui_init_completes(self):
        """MetalGUI(design) must build cleanly on a real display."""
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")
        self._run_snippet(_SNIPPET, "MARKER_INIT_OK")

    def test_metalgui_init_self_heals_across_kernel_switch(self):
        """The exact multi-Jupyter-kernel sequence RhinoHand hit must
        never stay broken past one extra launch.

        (https://github.com/qiskit-community/qiskit-metal/issues/1048#issuecomment-4914073094)
        kernel A closes its GUI (saves state) -> kernel B opens its own
        GUI reading that state -> kernel C opens a GUI later.

        We deliberately do NOT assert kernel B succeeds: Qt's
        cross-process ``restoreState()`` is the thing issue #1048 is
        chasing in the first place, and asserting it always succeeds
        reintroduces the exact flakiness that failed CI on macOS earlier
        in this PR's history (a real native abort during restore, by
        design, cannot be caught by our Python try/except). What we
        DO assert is the actual promise made to users: whatever
        happened to B, kernel C must build cleanly. That's true whether
        B succeeded (state intact, fingerprint still matches, plain
        restore) or B crashed mid-restore (cookie left set, C's
        crash-cookie check discards state and starts fresh).
        """
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")
        _clear_persisted_settings()
        try:
            self._run_snippet(_SAVE_STATE_SNIPPET, "MARKER_SAVED_STATE")
            # Kernel B: allowed to crash. Not asserted either way.
            self._run_snippet(
                _RESTORE_ONLY_SNIPPET, "MARKER_RESTORED_OK", require_success=False
            )
            # Kernel C: must always succeed, regardless of B's outcome.
            self._run_snippet(_RESTORE_ONLY_SNIPPET, "MARKER_RESTORED_OK")
        finally:
            _clear_persisted_settings()

    def test_metalgui_init_with_stale_fingerprint(self):
        """A persisted display fingerprint that no longer matches the
        current display must be discarded -- and ONLY the fingerprint
        mismatch should be what triggers the clear (metal_version and
        qt_version are left matching the real environment, so this
        test isolates the fingerprint branch specifically instead of
        falling through the earlier version checks)."""
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")
        _clear_persisted_settings()
        try:
            self._run_snippet(_SAVE_STATE_SNIPPET, "MARKER_SAVED_STATE")
            before = _read_persisted_settings()
            self.assertTrue(
                before["geometry"],
                "sanity check: save_window_settings should have persisted "
                "non-empty geometry bytes",
            )

            # Tamper with exactly one field, from the test process,
            # directly on disk. metal_version / qt_version are left
            # alone so they still match -- only the fingerprint differs.
            s = _settings()
            s.setValue("display_fingerprint", "BOGUS_FINGERPRINT_FOR_TEST")
            s.sync()

            self._run_snippet(_RESTORE_ONLY_SNIPPET, "MARKER_RESTORED_OK")

            after = _read_persisted_settings()
            self.assertFalse(
                after["geometry"],
                "fingerprint mismatch should have cleared persisted "
                f"settings (geometry should be empty again); got: {after}",
            )
        finally:
            _clear_persisted_settings()

    def test_metalgui_init_recovers_from_crashed_restore(self):
        """A leftover ``restore_in_progress`` cookie must trigger a
        clean-slate recovery -- and ONLY the cookie should be what
        triggers the clear (metal_version, qt_version, and
        display_fingerprint are all left matching the real environment,
        isolating the crash-cookie branch specifically)."""
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")
        _clear_persisted_settings()
        try:
            self._run_snippet(_SAVE_STATE_SNIPPET, "MARKER_SAVED_STATE")
            before = _read_persisted_settings()
            self.assertTrue(
                before["geometry"],
                "sanity check: save_window_settings should have persisted "
                "non-empty geometry bytes",
            )
            self.assertFalse(
                before["restore_in_progress"],
                "sanity check: save_window_settings must not touch the "
                "restore_in_progress cookie",
            )

            # Simulate a previous launch that died mid-restore: leave
            # the cookie set. Everything else (version/qt/fingerprint)
            # is untouched and still matches the real environment.
            s = _settings()
            s.setValue("restore_in_progress", True)
            s.sync()

            self._run_snippet(_RESTORE_ONLY_SNIPPET, "MARKER_RESTORED_OK")

            after = _read_persisted_settings()
            self.assertFalse(
                after["restore_in_progress"],
                "crash-cookie recovery should have cleared the cookie",
            )
            self.assertFalse(
                after["geometry"],
                "crash-cookie recovery should have cleared persisted "
                f"settings entirely (geometry should be empty again); got: {after}",
            )
        finally:
            _clear_persisted_settings()


if __name__ == "__main__":
    unittest.main(verbosity=2)
