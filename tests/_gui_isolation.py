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

Selection: ``conftest`` runs the swap after ``-k``/``-m``/nodeid deselection,
so the child is handed exactly the node ids that survived. A module whose
tests all skip reports as skipped, not passed.

Not covered by ``--cov`` in the parent (the child is a separate process).
"""

import os
import re
import signal
import subprocess
import sys

import pytest

from tests._crash_output import crash_excerpt

CHILD_ENV = "QISKIT_METAL_ISOLATED_CHILD"
CHILD_TIMEOUT_S = 900

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

_NTSTATUS = {
    0xC0000005: "STATUS_ACCESS_VIOLATION",
    0xC0000409: "STATUS_STACK_BUFFER_OVERRUN",
    0xC000001D: "STATUS_ILLEGAL_INSTRUCTION",
}


def describe_returncode(rc: int) -> str:
    """Name a child's exit status: POSIX signal, or Windows NTSTATUS."""
    if rc < 0:
        try:
            return f"killed by {signal.Signals(-rc).name}"
        except ValueError:
            return f"killed by signal {-rc}"
    if rc >= 0xC0000000:
        return _NTSTATUS.get(rc, f"NTSTATUS 0x{rc:08X}") + " (native crash)"
    return f"exit code {rc}"


def _text(value) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def run_child(args, env, timeout):
    """Run a child pytest in its own process group; kill the group on timeout."""
    popen_kw = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        **popen_kw,
    ) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                proc.kill()
            else:
                os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
            return None, out, err
    return proc.returncode, out, err


class IsolatedModuleFailure(Exception):
    """The isolated child pytest run failed or died."""


class IsolatedModuleItem(pytest.Item):
    """One item standing in for the selected tests of an isolated module."""

    def __init__(self, *, module_path, nodeids, **kwargs):
        super().__init__(**kwargs)
        self.module_path = module_path
        self.nodeids = nodeids

    def runtest(self):
        env = dict(os.environ)
        env[CHILD_ENV] = "1"
        rootdir = str(self.config.rootpath)
        args = [
            sys.executable,
            "-X",
            "faulthandler",
            "-m",
            "pytest",
            *self.nodeids,
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=",  # plain output: pytest-rich can swallow the -r summary
            "-rfEs",
            "--rootdir",
            rootdir,
        ]
        rc, out, err = run_child(args, env, CHILD_TIMEOUT_S)
        name = self.module_path.name
        rerun = (
            f"Re-run in-process with: {CHILD_ENV}=1 python -m pytest "
            f"{' '.join(self.nodeids[:1])}"
        )
        if rc is None:
            raise IsolatedModuleFailure(
                f"{name} timed out after {CHILD_TIMEOUT_S}s in its child process "
                "(process group killed).\n"
                f"{rerun}\n"
                f"--- child stdout (tail) ---\n{_text(out)[-4000:]}\n"
                f"--- child stderr ---\n{crash_excerpt(_text(err))}"
            )
        if rc != 0:
            raise IsolatedModuleFailure(
                f"{name} failed in its child process ({describe_returncode(rc)}).\n"
                f"{rerun}\n"
                f"--- child stdout (tail) ---\n{out[-4000:]}\n"
                f"--- child stderr ---\n{crash_excerpt(err)}"
            )
        summary = out.strip().splitlines()[-1] if out.strip() else ""
        if re.search(r"\bskipped\b", summary) and not re.search(r"\bpassed\b", summary):
            pytest.skip(f"every test in {name} skipped in the child: {summary}")

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, IsolatedModuleFailure):
            return str(excinfo.value)
        return super().repr_failure(excinfo, style)

    def reportinfo(self):
        return self.path, 0, f"{self.module_path.name} (isolated child process)"


def isolate_modules(items):
    """Replace each isolated module's selected items with one child-run item."""
    if os.environ.get(CHILD_ENV):
        return
    kept, groups, order = [], {}, []
    for item in items:
        name = item.path.name
        if name not in ISOLATED_MODULES:
            kept.append(item)
            continue
        if name not in groups:
            groups[name] = (item.getparent(pytest.Module), item.path, [])
            order.append(name)
            kept.append(name)  # placeholder, replaced below
        groups[name][2].append(item.nodeid)
    items[:] = [
        IsolatedModuleItem.from_parent(
            groups[k][0],
            name="isolated",
            module_path=groups[k][1],
            nodeids=groups[k][2],
        )
        if isinstance(k, str)
        else k
        for k in kept
    ]
