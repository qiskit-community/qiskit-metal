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

"""Resolving a QComponent source file to its class (issue #1178).

The GUI turns a file picked in the Library pane into a class via
``get_class_from_abs_file_path``. That used to slice the absolute path at
the first literal occurrence of ``"qiskit_metal"`` and import whatever
followed, which failed two ways:

* a component shipped by a *different* distribution raised
  ``ValueError: substring not found`` -- so external packages could never
  be used, which is the blocker behind issue #1178;
* any path merely *containing* the name (a checkout under
  ``~/qiskit_metal_dev/``, a directory called
  ``qiskit_metal_experiments``) was sliced at the wrong offset and
  resolved to a module that does not exist -- a live bug for in-tree
  users with an unlucky directory name.

Resolution now walks up from the file to the package root via
``__init__.py``, so it is independent of where the package is installed
and of what the surrounding directories are called.

These tests need PySide6 importable (the module under test lives in
``_gui``) but not a display -- nothing is shown.
"""

import os
import sys
import textwrap
import unittest


def _pyside_available():
    try:
        import PySide6  # noqa: F401
    except ImportError:
        return False
    return True


@unittest.skipUnless(
    _pyside_available(), "needs PySide6 (module under test is in _gui)"
)
class TestComponentPathResolution(unittest.TestCase):
    """Issue #1178 — path→module resolution must not depend on path spelling."""

    def setUp(self):
        from qiskit_metal._gui.utility.utils import (
            class_from_abs_file_path,
            module_path_from_abs_file_path,
        )

        self.module_path = module_path_from_abs_file_path
        self.get_class = class_from_abs_file_path

    @staticmethod
    def _write_external_component(tmp):
        """Create an importable package with a QComponent in it.

        Returns the package directory's parent (to put on ``sys.path``)
        and the absolute path of the component file.
        """
        pkg = os.path.join(tmp, "my_solver_pkg")
        os.makedirs(pkg)
        open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8").close()
        component = os.path.join(pkg, "my_component.py")
        with open(component, "w", encoding="utf-8") as handle:
            handle.write(
                textwrap.dedent(
                    """
                    from qiskit_metal.qlibrary.core import QComponent

                    class MyExternalComponent(QComponent):
                        TOOLTIP = "external tooltip"
                        default_options = dict()

                        def make(self):
                            pass
                    """
                )
            )
        return component

    def test_in_tree_component_still_resolves(self):
        """The path that already worked must keep working."""
        from qiskit_metal import qlibrary

        path = os.path.join(
            os.path.dirname(qlibrary.__file__), "qubits", "transmon_pocket.py"
        )

        self.assertEqual(
            self.module_path(path),
            "qiskit_metal.qlibrary.qubits.transmon_pocket",
        )
        self.assertEqual(self.get_class(path).__name__, "TransmonPocket")

    def test_component_in_an_external_package_resolves(self):
        """A QComponent from another distribution must resolve (issue #1178).

        Previously raised ``ValueError: substring not found``, because the
        path contained no ``qiskit_metal`` segment to slice on.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            pkg = os.path.join(tmp, "my_solver_pkg")
            os.makedirs(pkg)
            open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8").close()
            component = os.path.join(pkg, "my_component.py")
            with open(component, "w", encoding="utf-8") as handle:
                handle.write(
                    textwrap.dedent(
                        """
                        from qiskit_metal.qlibrary.core import QComponent

                        class MyExternalComponent(QComponent):
                            default_options = dict()

                            def make(self):
                                pass
                        """
                    )
                )

            self.assertEqual(self.module_path(component), "my_solver_pkg.my_component")

            sys.path.insert(0, tmp)
            try:
                self.assertEqual(
                    self.get_class(component).__name__, "MyExternalComponent"
                )
            finally:
                sys.path.remove(tmp)
                sys.modules.pop("my_solver_pkg.my_component", None)
                sys.modules.pop("my_solver_pkg", None)

    def test_lookalike_directory_name_is_not_mistaken_for_the_package(self):
        """A path merely *containing* 'qiskit_metal' must not be sliced on it.

        ``~/qiskit_metal_experiments/foo.py`` used to resolve to the
        module ``qiskit_metal_experiments.foo`` and raise
        ``ModuleNotFoundError``. It is not in a package at all, so the
        correct answer is a clear error naming the real problem.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            directory = os.path.join(tmp, "qiskit_metal_experiments")
            os.makedirs(directory)
            stray = os.path.join(directory, "foo.py")
            with open(stray, "w", encoding="utf-8") as handle:
                handle.write("x = 1\n")

            with self.assertRaises(ValueError) as ctx:
                self.module_path(stray)

            self.assertIn("importable package", str(ctx.exception))

    def test_nested_package_walks_to_the_true_root(self):
        """Resolution must climb every level that has an __init__.py."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            deep = os.path.join(tmp, "outer", "middle", "inner")
            os.makedirs(deep)
            for level in ("outer", os.path.join("outer", "middle"), deep):
                init = os.path.join(tmp, level, "__init__.py")
                open(init, "w", encoding="utf-8").close()
            leaf = os.path.join(deep, "thing.py")
            open(leaf, "w", encoding="utf-8").close()

            self.assertEqual(self.module_path(leaf), "outer.middle.inner.thing")

    def test_both_call_sites_share_one_implementation(self):
        """The delegate and the entry window must resolve identically.

        ``delegate_qlibrary.LibraryDelegate.get_class_from_abs_file_path``
        held a byte-identical copy of the old substring logic, so fixing
        only the entry window left the Library-pane tooltip path broken.
        Its bare ``except`` turned that into a silently empty tooltip
        rather than a visible error, which is why it went unnoticed.
        """
        import tempfile

        from qiskit_metal._gui.widgets.create_component_window import (
            parameter_entry_window as pew,
        )
        from qiskit_metal._gui.widgets.qlibrary_display.delegate_qlibrary import (
            LibraryDelegate,
        )

        with tempfile.TemporaryDirectory() as tmp:
            component = self._write_external_component(tmp)

            sys.path.insert(0, tmp)
            try:
                via_delegate = LibraryDelegate.get_class_from_abs_file_path(
                    None, component
                )
                via_entry_window = pew.get_class_from_abs_file_path(component)
            finally:
                sys.path.remove(tmp)
                sys.modules.pop("my_solver_pkg.my_component", None)
                sys.modules.pop("my_solver_pkg", None)

            self.assertIsNotNone(
                via_delegate,
                msg=(
                    "the Library-pane delegate could not resolve an external "
                    "component; it likely still has its own copy of the "
                    "substring logic (issue #1178)"
                ),
            )
            self.assertIs(via_delegate, via_entry_window)
            self.assertEqual(via_delegate.TOOLTIP, "external tooltip")


if __name__ == "__main__":
    unittest.main(verbosity=2)
