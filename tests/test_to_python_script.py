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
import unittest

import numpy as np

import qiskit_metal
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


class _StubMetalGUI:
    """No-op stand-in for ``MetalGUI`` so the exported script's
    ``gui = MetalGUI(design); gui.rebuild(); gui.autoscale()`` calls
    don't try to construct a Qt window in the test process."""

    def __init__(self, design):  # noqa: D401
        self.design = design

    def rebuild(self):
        pass

    def autoscale(self):
        pass


def _exec_exported_script(script: str) -> dict:
    """Execute ``script`` in a clean namespace with ``MetalGUI`` stubbed.

    Returns the resulting global namespace so tests can inspect what was
    bound (e.g. ``design``, ``gui``). Re-raises any exception so the
    failing test reports the actual error.
    """
    original = qiskit_metal.__dict__.get("MetalGUI", None)
    qiskit_metal.MetalGUI = _StubMetalGUI
    try:
        ns: dict = {"__name__": "__exported__"}
        exec(compile(script, "<exported.metal.py>", "exec"), ns)
        return ns
    finally:
        if original is None:
            qiskit_metal.__dict__.pop("MetalGUI", None)
        else:
            qiskit_metal.MetalGUI = original


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
