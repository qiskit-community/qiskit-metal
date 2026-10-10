# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""The left dock panel must be able to shrink to a narrow width.

The six left-hand docks (QComponents, Library, Pins, Variables, Chip, Layers)
are tabified into one group, and QMainWindow gives that group a QTabBar. On
macOS the native style sets ``SH_TabBar_PreferNoArrows``, so the tab bar has
no scroll arrows and its minimum width is the sum of every tab -- measured at
432 px on macOS -- which pinned the splitter so the left panel could not be
dragged any narrower. ``QMainWindowExtensionBase.childEvent`` now turns on
scroll buttons for every dock tab bar the main window creates.

Headless defaults hide the bug: the offscreen/Fusion style already uses
scroll arrows, so a plain offscreen run passes before and after the fix. The
child process therefore gives each dock tab bar a proxy style that reports
``SH_TabBar_PreferNoArrows`` like macOS does (``QTabBar`` re-reads the hint
on a style change, so the bars lose their arrows), then switches dock tabs
the way a user does. That emits ``tabifiedDockWidgetActivated``, which runs
the product's tab-bar sweep. Without the sweep the bars keep the sum-of-tabs
floor (432 px on macOS, about 350 px under ``offscreen``).

The proxy is applied to the existing tab bars after ``MetalGUI`` is built and
removed again before teardown, never installed as the application style. A
Python ``styleHint`` on the application style runs for every style query of
every widget -- about 4,000 calls per ``MetalGUI`` start, many from inside
C++ widget constructors (``QTabBar`` queries this very hint while it is being
built), each wrapping the half-built widget and setting a dynamic property on
it. That is the Python-in-Qt's-construction-path hazard of failure mode 5 in
``docs/architecture/gui_crash_defenses.md``; the app-wide version of this
test crashed the child intermittently on CI (access violation inside
``styleHint`` during ``set_design``; ``rc=-6`` after the tab bars were
measured). Product code installs no Python style.

The full MetalGUI is built in a subprocess, like the other full-GUI tests,
so a native teardown crash cannot take down the pytest process.
"""

import os
import re
import subprocess
import sys

import pytest

pytest.importorskip("PySide6")

# Left panel must be able to reach this width (the user-facing goal is
# "roughly 200 px or less").
MAX_LEFT_MIN_WIDTH = 200

_SNIPPET = """
import faulthandler, sys
faulthandler.enable()

from PySide6.QtCore import QElapsedTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QProxyStyle, QStyle, QTabBar


class MacLikeTabBarStyle(QProxyStyle):
    # Emulate the macOS style: tab bars prefer no scroll arrows.
    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.SH_TabBar_PreferNoArrows:
            return 1
        return super().styleHint(hint, option, widget, returnData)


app = QApplication.instance() or QApplication([])

from qiskit_metal import designs
from qiskit_metal._gui.main_window import MetalGUI


def pump(ms):
    elapsed = QElapsedTimer()
    elapsed.start()
    while elapsed.elapsed() < ms:
        app.processEvents(QEventLoop.AllEvents, 50)
    app.processEvents()


gui = MetalGUI(designs.DesignPlanar())
# Module-level: setStyle() does not take ownership, so this reference keeps
# the style alive for as long as any bar uses it.
mac_style = MacLikeTabBarStyle()
styled_bars = []
try:
    pump(300)
    mw = gui.main_window
    # Style only the dock tab bars, after construction. QTabBar re-reads
    # SH_TabBar_PreferNoArrows on the style change, so each bar now has no
    # scroll arrows, as a macOS-born bar does.
    for b in mw.findChildren(QTabBar, options=Qt.FindDirectChildrenOnly):
        b.setStyle(mac_style)
        styled_bars.append(b)
    pump(100)
    # Switch dock tabs the way a user does: QMainWindow emits
    # tabifiedDockWidgetActivated, which runs the product's tab-bar sweep.
    for b in styled_bars:
        if b.isVisible() and b.count() > 1:
            b.setCurrentIndex((b.currentIndex() + 1) % b.count())
    pump(200)
    # Measure only docks actually on screen: a dock behind another tab
    # keeps whatever width it last had, so it says nothing about the
    # area's current floor.
    left = [
        d
        for d in mw.findChildren(QDockWidget)
        if mw.dockWidgetArea(d) == Qt.LeftDockWidgetArea
        and d.isVisible()
        and not d.visibleRegion().isEmpty()
    ]
    print("LEFT_DOCKS", len(left), flush=True)
    bars = [b for b in styled_bars if b.isVisible()]
    print("TABBARS", len(bars), flush=True)
    for b in bars:
        print("TABBAR_SCROLL", b.usesScrollButtons(), flush=True)
        print("TABBAR_MSH", b.minimumSizeHint().width(), flush=True)
    # Ask for an impossibly narrow left area; Qt clamps to the real minimum.
    mw.resizeDocks(left, [20] * len(left), Qt.Horizontal)
    pump(200)
    print("LEFT_WIDTH", max(d.width() for d in left), flush=True)
    print("MARKER_OK", flush=True)
finally:
    # Back to the application style before teardown, so no Python style
    # is in use while the widgets are destroyed.
    for b in styled_bars:
        b.setStyle(None)
    gui.main_window.force_close = True
    gui.main_window.close()
    pump(200)
sys.exit(0)
"""


def test_left_dock_area_can_shrink_below_threshold():
    env = dict(os.environ)
    env.pop("QISKIT_METAL_HEADLESS", None)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env["QISKIT_METAL_GUI_FORCE_CLOSE"] = "1"
    proc = subprocess.run(
        [sys.executable, "-X", "faulthandler", "-c", _SNIPPET],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    out = proc.stdout
    assert "MARKER_OK" in out, (
        f"GUI child did not finish (rc={proc.returncode}).\n"
        f"stdout:\n{out[-2000:]}\nstderr:\n{proc.stderr[-2000:]}"
    )

    assert "already deleted" not in out + proc.stderr

    n_bars = int(re.search(r"TABBARS (\d+)", out).group(1))
    assert n_bars >= 1, "expected the tabified left docks to have a tab bar"
    assert "TABBAR_SCROLL False" not in out, (
        "a dock tab bar has scroll buttons disabled; on macOS its minimum "
        "width is then the sum of all tabs"
    )
    for msh in re.findall(r"TABBAR_MSH (\d+)", out):
        assert int(msh) < MAX_LEFT_MIN_WIDTH, f"dock tab bar min width {msh} px"

    assert int(re.search(r"LEFT_DOCKS (\d+)", out).group(1)) >= 1
    width = int(re.search(r"LEFT_WIDTH (\d+)", out).group(1))
    assert width < MAX_LEFT_MIN_WIDTH, (
        f"left dock area cannot shrink below {width} px (want < {MAX_LEFT_MIN_WIDTH})"
    )
