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

"""Regression coverage for ``QDesign.to_python_script``.

Until PR #1043 there was zero automated coverage on the GUI-export-to-Python
path. That left two real bugs un-guarded:

1. **Issue #1042** — when a component option contained a numpy array, the
   exported ``.metal.py`` serialized it as ``array([...])`` (numpy ndarray's
   ``repr``) but never imported ``array``. Running the script raised
   ``NameError: name 'array' is not defined`` immediately. PR #1043 added
   a conditional ``from numpy import array`` when the body contains
   ``"array("``; these tests guard that fix from a future refactor of
   ``to_python_script``.

2. **Script-output validity in general** — without a "the output parses /
   executes" gate, nothing prevents a future option-serialization change
   from silently producing broken Python. The ``ast.parse`` + sandboxed
   ``exec`` tests below catch that class of regression too.

The sandboxed-exec tests substitute a no-op ``MetalGUI`` stub into the
``qiskit_metal`` module's namespace before ``exec`` so the exported
script doesn't actually try to construct a Qt window. That makes the
tests runnable on the lite install (no PySide6).
"""

from __future__ import annotations

import ast
import sys
import unittest

import numpy as np

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


def _make_design_with_numpy_array_option() -> "designs.DesignPlanar":
    """Build a minimal design whose component options include a numpy array.

    Mirrors the failure shape from issue #1042 (``RouteMixed.anchors`` with
    numpy values) but uses ``TransmonPocket`` -- a no-extras-required
    component already exercised by the lite-CI smoke test -- with a
    manually-injected ndarray option, so the test runs on any install.
    """
    design = designs.DesignPlanar()
    q = TransmonPocket(
        design,
        "Q1",
        options=dict(connection_pads=dict(a=dict())),
    )
    q.options["custom_anchor"] = np.array([1.0, 2.0])
    return design


class _StubQApp:
    """Stand-in for the ``QApplication`` at ``MetalGUI.qApp``.

    Records whether the exported script started the event loop instead of
    actually blocking on one, so the exec-based tests stay non-blocking and
    runnable on the lite install.
    """

    def __init__(self):
        self.exec_calls = 0

    def exec(self):
        self.exec_calls += 1
        return 0


class _StubMetalGUI:
    """No-op stand-in for ``MetalGUI`` so the exported script's
    ``gui = MetalGUI(design); gui.rebuild(); gui.autoscale()`` calls
    don't try to construct a Qt window in the test process.

    ``qApp`` mirrors the real ``MetalGUI`` attribute (set in
    ``main_window_base._setup_qApp``); pass ``qapp=None`` to emulate a
    headless machine where no ``QApplication`` could be created.
    """

    def __init__(self, design, qapp: "_StubQApp | None" = None):  # noqa: D401
        self.design = design
        self.qApp = _StubQApp() if qapp is None else qapp

    def rebuild(self):
        pass

    def autoscale(self):
        pass


class _StubMetalGUINoQApp(_StubMetalGUI):
    """``MetalGUI`` whose ``qApp`` is None -- the headless case."""

    def __init__(self, design):
        super().__init__(design)
        self.qApp = None


def _exec_exported_script(
    script: str,
    run_name: str = "__exported__",
    gui_cls: type = _StubMetalGUI,
) -> dict:
    """Execute ``script`` in a clean namespace with ``MetalGUI`` stubbed.

    The patch must target the ``qiskit_metal`` MODULE attribute -- the
    exported script runs ``from qiskit_metal import designs, MetalGUI``
    which resolves ``MetalGUI`` from the module's namespace, not the
    caller's globals. We grab the live module via ``sys.modules`` (rather
    than ``import qiskit_metal``) to avoid the dual ``import`` /
    ``from import`` style smell on the same package.

    ``run_name`` sets the script's ``__name__``; pass ``"__main__"`` to
    exercise the standalone-run path that starts the Qt event loop.
    ``gui_cls`` swaps in a different ``MetalGUI`` stub (e.g. the headless
    no-``qApp`` variant).

    Returns the resulting global namespace so tests can inspect what was
    bound (e.g. ``design``, ``gui``). Re-raises any exception so the
    failing test reports the actual error.
    """
    qm = sys.modules["qiskit_metal"]
    original = qm.__dict__.get("MetalGUI", None)
    qm.MetalGUI = gui_cls
    try:
        ns: dict = {"__name__": run_name}
        exec(compile(script, "<exported.metal.py>", "exec"), ns)
        return ns
    finally:
        if original is None:
            qm.__dict__.pop("MetalGUI", None)
        else:
            qm.MetalGUI = original


class TestToPythonScriptStructure(unittest.TestCase):
    """``to_python_script`` always produces the expected skeleton."""

    def test_baseline_script_has_minimum_structure(self):
        """For any non-empty design, the script must wire up a GUI and
        rebuild it. Catches a future refactor that drops the header/footer."""
        design = designs.DesignPlanar()
        TransmonPocket(design, "Q1", options=dict(connection_pads=dict(a=dict())))

        script = design.to_python_script()

        self.assertIn("from qiskit_metal import designs, MetalGUI", script)
        self.assertIn("design = designs.DesignPlanar()", script)
        self.assertIn("MetalGUI(design)", script)
        self.assertIn("gui.rebuild()", script)
        self.assertIn("gui.autoscale()", script)

    def test_script_is_syntactically_valid(self):
        """ast.parse must accept the script unconditionally -- any
        SyntaxError is an outright regression."""
        design = _make_design_with_numpy_array_option()

        script = design.to_python_script()

        try:
            ast.parse(script)
        except SyntaxError as e:
            self.fail(
                f"to_python_script output is not valid Python:\n{e}\n\nScript:\n{script}"
            )


class TestQiskitMetalImport(unittest.TestCase):
    """Issue #1157 — the generated script must ``import qiskit_metal``.

    When a component's ``name`` is not a valid Python identifier,
    ``QComponent.to_script`` falls back to a variable name built from the
    component's full module path (``qiskit_metal.qlibrary...<random>``). Without
    a top-level ``import qiskit_metal`` the exported script then raises
    ``NameError: name 'qiskit_metal' is not defined`` on that assignment.
    """

    @staticmethod
    def _design_with_non_identifier_name() -> "designs.DesignPlanar":
        # A name starting with a digit is not a valid identifier, so
        # to_script uses the module-path fallback that references qiskit_metal.
        design = designs.DesignPlanar()
        TransmonPocket(design, "7q", options=dict(connection_pads=dict(a=dict())))
        return design

    def test_script_imports_qiskit_metal(self):
        """The header must import ``qiskit_metal`` outright, not only
        ``from qiskit_metal import ...`` (regression of issue #1157)."""
        script = self._design_with_non_identifier_name().to_python_script()
        self.assertIn("import qiskit_metal", script)

    def test_non_identifier_name_executes_without_NameError(self):
        """The reporter's failure was a NameError on a
        ``qiskit_metal.qlibrary...`` assignment. Exec the script and assert it
        completes."""
        script = self._design_with_non_identifier_name().to_python_script()
        # sanity: the fallback path that needs the import is actually taken
        self.assertIn("qiskit_metal.qlibrary", script)
        try:
            _exec_exported_script(script)
        except NameError as e:
            self.fail(
                f"Exported script raised NameError -- regression of #1157: {e}\n\n"
                f"Script:\n{script}"
            )


class TestQtEventLoop(unittest.TestCase):
    """PR #1159 — the exported script starts a Qt event loop so a standalone
    run keeps the window open, but must stay safe on every install variant.

    The loop is guarded on ``__name__ == "__main__"`` and on ``gui.qApp`` being
    non-None, so that:

    * ``python my_chip_design.py`` blocks on the loop (window stays open),
    * importing the file, or exec'ing it inside a session that already runs a
      Qt loop (Jupyter/IPython ``%gui qt``), does NOT block,
    * a headless machine where no ``QApplication`` could be built (``qApp`` is
      None) doesn't ``AttributeError``.
    """

    @staticmethod
    def _script() -> str:
        design = designs.DesignPlanar()
        TransmonPocket(design, "Q1", options=dict(connection_pads=dict(a=dict())))
        return design.to_python_script()

    def test_uses_exec_not_deprecated_alias(self):
        """PySide6 exposes ``exec()``; ``exec_()`` is the deprecated alias and
        emits a DeprecationWarning."""
        script = self._script()
        self.assertIn("gui.qApp.exec()", script)
        self.assertNotIn("exec_()", script)

    def test_event_loop_is_guarded_on_main(self):
        """The loop must be inside an ``if __name__ == "__main__"`` guard so
        importing the exported script never blocks."""
        script = self._script()
        self.assertIn('if __name__ == "__main__"', script)

    def test_not_run_as_main_does_not_start_loop(self):
        """Imported / exec'd (not standalone): must NOT block on the loop."""
        ns = _exec_exported_script(self._script(), run_name="__exported__")
        self.assertEqual(ns["gui"].qApp.exec_calls, 0)

    def test_run_as_main_starts_loop(self):
        """Standalone run: the event loop must actually start, otherwise the
        window flashes and closes (the bug PR #1159 fixed)."""
        ns = _exec_exported_script(self._script(), run_name="__main__")
        self.assertEqual(ns["gui"].qApp.exec_calls, 1)

    def test_headless_no_qapp_does_not_raise(self):
        """If no QApplication could be created, ``gui.qApp`` is None; the
        script must skip the loop rather than AttributeError."""
        ns = _exec_exported_script(
            self._script(), run_name="__main__", gui_cls=_StubMetalGUINoQApp
        )
        self.assertIsNone(ns["gui"].qApp)


class TestNumpyArrayImport(unittest.TestCase):
    """Issue #1042 — the numpy.array import must be present iff used."""

    def test_numpy_array_in_options_triggers_import(self):
        """When a component option is a numpy ndarray, the script must
        ``from numpy import array`` so the serialized ``array(...)`` literal
        resolves at runtime."""
        design = _make_design_with_numpy_array_option()

        script = design.to_python_script()

        self.assertIn(
            "array(",
            script,
            msg="ndarray option should be serialized as array(...); "
            "if this fails, pprint behavior changed and the import-detection "
            "heuristic in to_python_script needs updating too.",
        )
        self.assertIn(
            "from numpy import array",
            script,
            msg="missing numpy import would NameError when the script runs "
            "(regression of issue #1042)",
        )

    def test_no_numpy_array_no_spurious_import(self):
        """When no option uses numpy, the script must NOT import
        ``array`` -- a spurious import is a minor wart but should be caught
        if the substring heuristic in to_python_script ever broadens
        unintentionally."""
        design = designs.DesignPlanar()
        TransmonPocket(design, "Q1", options=dict(connection_pads=dict(a=dict())))

        script = design.to_python_script()

        self.assertNotIn(
            "array(",
            script,
            msg="no ndarray option should appear in this design's serialized body",
        )
        self.assertNotIn(
            "from numpy import array",
            script,
            msg="numpy import should be omitted when not needed",
        )

    def test_script_executes_without_NameError(self):
        """End-to-end: the exact failure mode of #1042 was a NameError on
        the very first option-parse line. Exec the script in a sandboxed
        namespace and assert it completes."""
        design = _make_design_with_numpy_array_option()

        script = design.to_python_script()

        try:
            ns = _exec_exported_script(script)
        except NameError as e:
            self.fail(
                f"Exported script raised NameError -- regression of #1042: {e}\n\n"
                f"Script:\n{script}"
            )

        # Sanity: the stub MetalGUI was constructed, so the script reached
        # its end. Without this assertion a silent return-mid-script would
        # masquerade as a pass.
        self.assertIsInstance(ns.get("gui"), _StubMetalGUI)


if __name__ == "__main__":
    unittest.main(verbosity=2)
