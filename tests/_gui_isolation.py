# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Run in-process-Qt test files in a child pytest, one child per file.

These files build a real ``QApplication`` and widgets inside the test
process. A native crash there (the intermittent ``rc=-11`` use-after-free
class, issue #1048) kills the whole pytest run and cancels the CI matrix --
which is how main's Python 3.14 macOS job died. The tests themselves stay
untouched; ``conftest.py`` swaps each listed module's items for one
``IsolatedModuleItem`` that runs the module in a child process, so a native
death fails that one item with the child's crash excerpt and everything else
carries on.

The child sets ``QISKIT_METAL_ISOLATED_CHILD`` and runs the file's tests
normally, with per-test results in the failure output. Run a file directly
(``pytest tests/test_gui_layer_panel.py``) and it is isolated too; run with
``QISKIT_METAL_ISOLATED_CHILD=1`` to opt out and debug in-process.

Not covered by ``--cov`` in the parent (the child is a separate process).
"""

import os
import subprocess
import sys

import pytest

from tests._crash_output import crash_excerpt

CHILD_ENV = "QISKIT_METAL_ISOLATED_CHILD"

#: Test modules that construct a QApplication / widgets in-process.
ISOLATED_MODULES = frozenset(
    {
        "test_gui_autoscale.py",
        "test_gui_chip_editor.py",
        "test_gui_click_select.py",
        "test_gui_component_labels.py",
        "test_gui_expanding_toolbar.py",
        "test_gui_layer_panel.py",
        "test_gui_logger_lifecycle.py",
        "test_gui_pin_completer.py",
        "test_gui_qlibrary_pane.py",
        "test_gui_statusbar_hover.py",
        "test_gui_statusbar_widgets.py",
        "test_to_python_script.py",
    }
)


class IsolatedModuleItem(pytest.Item):
    """One item standing in for every test of an isolated module."""

    def __init__(self, *, module_path, **kwargs):
        super().__init__(**kwargs)
        self.module_path = module_path

    def runtest(self):
        env = dict(os.environ)
        env[CHILD_ENV] = "1"
        proc = subprocess.run(
            [
                sys.executable,
                "-X",
                "faulthandler",
                "-m",
                "pytest",
                str(self.module_path),
                "-q",
                "--no-header",
                "-p",
                "no:cacheprovider",
                "-rfE",
            ],
            capture_output=True,
            text=True,
            timeout=900,
            env=env,
        )
        if proc.returncode != 0:
            raise IsolatedModuleFailure(
                f"{self.module_path.name} failed in its child process "
                f"(rc={proc.returncode}; negative = killed by a signal, "
                "-11 = segfault).\n"
                f"--- child stdout (tail) ---\n{proc.stdout[-4000:]}\n"
                f"--- child stderr ---\n{crash_excerpt(proc.stderr)}"
            )

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, IsolatedModuleFailure):
            return str(excinfo.value)
        return super().repr_failure(excinfo, style)

    def reportinfo(self):
        return self.path, 0, f"{self.module_path.name} (isolated child process)"


class IsolatedModuleFailure(Exception):
    """The isolated child pytest run failed or died."""


def isolate_modules(items):
    """Replace each isolated module's items with a single child-run item."""
    if os.environ.get(CHILD_ENV):
        return
    kept, seen = [], {}
    for item in items:
        name = item.path.name
        if name not in ISOLATED_MODULES:
            kept.append(item)
        elif name not in seen:
            module = item.getparent(pytest.Module)
            seen[name] = IsolatedModuleItem.from_parent(
                module,
                name=f"{name}::isolated",
                module_path=item.path,
            )
            kept.append(seen[name])
    items[:] = kept
