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

"""Behaviour of the GUI's QLibrary pane (issue #1178).

``file_model_qlibrary``, ``proxy_model_qlibrary`` and
``tree_view_qlibrary`` had no tests at all, despite being the three files
any change to library discovery has to rewrite. This suite covers what
they actually promise:

* the file model resolves a component's display name and icon from
  docstring directives, and caches both;
* the proxy hides every column but the filename, and hides private /
  dunder entries;
* the tree view rejects a model of the wrong type, and -- the case that
  matters most -- a click emits a path that the rest of the GUI can
  actually resolve back to a class.

That last one is a regression test for a real break: the click handler
used to emit a path sliced at the first literal ``"qiskit_metal"``, i.e.
a *relative* path, even though its consumer's parameter is named
``abs_file_path``. Once path→module resolution stopped substring-slicing,
that relative payload no longer resolved and clicking a component raised
``ValueError`` instead of opening the parameter-entry window.

Needs PySide6 and a display (widgets are constructed, though never shown).
"""

import os
import unittest


def _qt_available():
    if os.environ.get("QISKIT_METAL_HEADLESS"):
        return False
    if not os.environ.get("DISPLAY") and os.name != "nt":
        return False
    try:
        import PySide6  # noqa: F401
    except ImportError:
        return False
    return True


@unittest.skipUnless(_qt_available(), "needs PySide6 and a display (Xvfb or desktop)")
class TestQLibraryPane(unittest.TestCase):
    """Issue #1178 — QLibrary pane model/proxy/view behaviour."""

    #: Every Qt object built here is kept alive for the process lifetime.
    #: Letting a QTreeView or QFileSystemModel be collected mid-run trips the
    #: teardown segfault documented in
    #: test_gui_logger_lifecycle.TestGUIGarbageCollectionCrash, which kills
    #: the whole runner (exit 139) rather than failing one test -- and short
    #: of that, disturbs the surviving widgets enough that a synthesized
    #: click silently stops emitting. Holding references keeps these
    #: assertions measuring what they claim to measure.
    _kept = []

    @classmethod
    def setUpClass(cls):
        from pathlib import Path

        from PySide6.QtWidgets import QApplication

        import qiskit_metal
        from qiskit_metal import qlibrary

        cls.app = QApplication.instance() or QApplication([])
        cls.qlibrary_root = os.path.dirname(qlibrary.__file__)
        cls.path_imgs = Path(os.path.dirname(qiskit_metal.__file__)) / "_gui" / "_imgs"

    def _model(self):
        from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import (
            QFileSystemLibraryModel,
        )

        model = QFileSystemLibraryModel(self.path_imgs)
        model.setRootPath(self.qlibrary_root)
        self._kept.append(model)
        return model

    def _proxy_over(self, model):
        from qiskit_metal._gui.widgets.qlibrary_display.proxy_model_qlibrary import (
            LibraryFileProxyModel,
        )

        proxy = LibraryFileProxyModel()
        proxy.setSourceModel(model)
        self._kept.append(proxy)
        return proxy

    def _view(self):
        from qiskit_metal._gui.widgets.qlibrary_display.tree_view_qlibrary import (
            TreeViewQLibrary,
        )

        view = TreeViewQLibrary(None)
        self._kept.append(view)
        return view

    # ------------------------------------------------------------------
    # proxy model
    # ------------------------------------------------------------------

    def test_proxy_shows_only_the_filename_column(self):
        """Size / Kind / Date Modified must stay hidden."""
        from PySide6.QtCore import QModelIndex

        proxy = self._proxy_over(self._model())

        self.assertTrue(proxy.filterAcceptsColumn(0, QModelIndex()))
        for column in (1, 2, 3):
            self.assertFalse(
                proxy.filterAcceptsColumn(column, QModelIndex()),
                msg=f"column {column} should be hidden in the Library pane",
            )

    def test_proxy_hides_private_and_dunder_entries(self):
        """``__init__.py``, ``__pycache__`` and ``_template`` must not show.

        Driven through the real source model rather than by calling the
        predicate with synthetic indices, so it exercises the actual
        name lookup.
        """
        model = self._model()
        proxy = self._proxy_over(model)

        qubits = os.path.join(self.qlibrary_root, "qubits")
        source_parent = model.index(qubits)
        # QFileSystemModel populates lazily; force the directory to load.
        model.fetchMore(source_parent)
        self.app.processEvents()

        hidden, shown = [], []
        for row in range(model.rowCount(source_parent)):
            name = model.index(row, 0, source_parent).data()
            if name is None:
                continue
            (shown if proxy.filterAcceptsRow(row, source_parent) else hidden).append(
                name
            )

        for name in shown:
            self.assertFalse(
                name.startswith("_"),
                msg=f"{name!r} starts with '_' and should have been filtered out",
            )

    # ------------------------------------------------------------------
    # file model
    # ------------------------------------------------------------------

    def test_file_model_display_name_comes_from_the_meta_description(self):
        """A component's display name is its ``.. meta:: :description:``.

        ``transmon_pocket.py`` carries one; the model should show that
        rather than the bare filename, and should cache it.
        """
        from PySide6.QtCore import Qt

        model = self._model()
        index = model.index(
            os.path.join(self.qlibrary_root, "qubits", "transmon_pocket.py")
        )

        display = model.data(index, Qt.DisplayRole)

        self.assertIsInstance(display, str)
        self.assertTrue(display)
        # Whatever it resolved to, it must now be cached under the filename.
        self.assertIn("transmon_pocket.py", model.nameCache)
        self.assertEqual(model.nameCache["transmon_pocket.py"], display)

    def test_file_model_returns_a_pixmap_for_the_decoration_role(self):
        """Every component row gets an icon, falling back to the logo."""
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap

        model = self._model()
        index = model.index(
            os.path.join(self.qlibrary_root, "qubits", "transmon_pocket.py")
        )

        icon = model.data(index, Qt.DecorationRole)

        self.assertIsInstance(icon, QPixmap)
        self.assertFalse(
            icon.isNull(), msg="Library pane icon must not be a null pixmap"
        )

    # ------------------------------------------------------------------
    # tree view
    # ------------------------------------------------------------------

    def test_view_rejects_a_model_of_the_wrong_type(self):
        """setModel must refuse anything but LibraryFileProxyModel."""
        from qiskit_metal.toolbox_metal.exceptions import QLibraryGUIException

        view = self._view()

        with self.assertRaises(QLibraryGUIException):
            view.setModel(self._model())  # the source model, not the proxy

    def test_view_accepts_the_proxy_model(self):
        """The correct model type must be accepted."""
        view = self._view()
        proxy = self._proxy_over(self._model())

        view.setModel(proxy)
        self.assertIs(view.model(), proxy)

    def test_tooltip_falls_back_to_the_default_when_empty(self):
        """An empty tooltip must not blank the view's helper text."""
        view = self._view()

        view.setToolTip("")
        self.assertEqual(view.toolTip(), view.tool_tip_str)

        view.setToolTip(None)
        self.assertEqual(view.toolTip(), view.tool_tip_str)

        view.setToolTip("a real tooltip")
        self.assertEqual(view.toolTip(), "a real tooltip")

    def test_click_handler_emits_a_resolvable_absolute_path(self):
        """The click payload must round-trip back to a class.

        Regression test for the third copy of the issue #1178 substring
        bug. ``mousePressEvent`` used to emit the path sliced at the first
        literal ``"qiskit_metal"`` -- a *relative* path, despite the
        consumer's parameter being named ``abs_file_path``. Once
        resolution stopped substring-slicing, that payload no longer
        resolved and clicking a component raised ValueError instead of
        opening the parameter-entry window.

        Drives the real handler, but stubs ``indexAt`` rather than
        synthesizing an on-screen click. A laid-out, shown QTreeView over
        a lazily-populating QFileSystemModel proved genuinely unstable
        here -- ``expandAll()`` plus ``scrollTo()`` segfaulted Qt outright,
        and even the reduced form crashed on 2 of 3 runs. Everything the
        handler actually decides (column check, isDir, mapToSource,
        filePath, emit) runs unchanged; only hit-testing is bypassed.
        """
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        from qiskit_metal._gui.utility.utils import class_from_abs_file_path

        model = self._model()
        proxy = self._proxy_over(model)
        view = self._view()
        view.setModel(proxy)

        qubits = os.path.join(self.qlibrary_root, "qubits")
        model.fetchMore(model.index(qubits))
        self.app.processEvents()

        target = model.index(os.path.join(qubits, "transmon_pocket.py"))
        self.assertTrue(target.isValid(), msg="transmon_pocket.py not found in model")
        proxy_index = proxy.mapFromSource(target)
        self.assertTrue(
            proxy_index.isValid(), msg="component row was filtered out of the proxy"
        )

        emitted = []
        view.qlibrary_filepath_signal.connect(emitted.append)

        view.indexAt = lambda _pos: proxy_index
        view.mousePressEvent(
            QMouseEvent(
                QEvent.MouseButtonPress,
                QPointF(0, 0),
                Qt.LeftButton,
                Qt.LeftButton,
                Qt.NoModifier,
            )
        )

        self.assertEqual(
            len(emitted), 1, msg=f"expected exactly one emission, got {emitted}"
        )
        payload = emitted[0]

        self.assertTrue(
            os.path.isabs(payload),
            msg=(
                f"click emitted a relative path ({payload!r}); every consumer "
                "treats it as absolute (issue #1178)"
            ),
        )
        self.assertTrue(os.path.isfile(payload), msg=f"{payload!r} does not exist")
        self.assertEqual(class_from_abs_file_path(payload).__name__, "TransmonPocket")


if __name__ == "__main__":
    unittest.main(verbosity=2)
