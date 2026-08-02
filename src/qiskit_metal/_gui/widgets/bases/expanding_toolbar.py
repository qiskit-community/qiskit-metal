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

from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar, QWidget, QSizePolicy, QToolButton


class QToolBarExpanding(QToolBar):
    """`QToolBarExpanding` class extends the `QToolBar` class.

    Example:
        ```toolbar = gui.ui.toolBarView```

    Args:
        QToolbar (QToolbar): QToolbar
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._toggle_btn_added = False
        # The spacer that pins the toggle to the end has to expand along
        # whichever axis the toolbar currently runs, so re-docking to a side
        # area has to re-point it.
        self.orientationChanged.connect(self._on_orientation_changed)

    def showEvent(self, event: QtCore.QEvent) -> None:
        """Add the toggle button to the far right the first time it is shown."""
        super().showEvent(event)
        if not self._toggle_btn_added:
            self._toggle_btn_added = True

            # Spacer to push button to the far end
            self._spacer = QWidget()
            self.addWidget(self._spacer)
            self._sync_spacer_policy()

            self._toggle_btn = QToolButton(self)
            self._toggle_btn.setCheckable(True)
            self._toggle_btn.setToolTip("Expand/collapse the toolbar")
            self._toggle_btn.clicked.connect(self.on_toggle_clicked)
            self.addWidget(self._toggle_btn)

            # Initialize in the contracted state
            self.contract_me()

    def _sync_spacer_policy(self):
        """Point the spacer's expanding axis along the toolbar's orientation."""
        spacer = getattr(self, "_spacer", None)
        if spacer is None:
            return
        if self.orientation() == Qt.Vertical:
            spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        else:
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def _on_orientation_changed(self, _orientation):
        """Re-point the spacer and redraw the arrow after a re-dock."""
        self._sync_spacer_policy()
        self.update_arrow_icon()

    def _sync_toggle_state(self, expanded: bool):
        """Keep the toggle button's checked state in step with the toolbar.

        ``expand_me`` / ``contract_me`` are public and can be called directly,
        not just from the button. Without this the button and the toolbar drift
        apart and the next user click re-applies the state it is already in --
        so the toolbar looks stuck until it is clicked a second time.
        """
        btn = getattr(self, "_toggle_btn", None)
        if btn is None or btn.isChecked() == expanded:
            return
        was_blocked = btn.blockSignals(True)
        btn.setChecked(expanded)
        btn.blockSignals(was_blocked)

    def update_arrow_icon(self):
        """Update the toggle button arrow to reflect the current expansion state."""
        if not hasattr(self, "_toggle_btn"):
            return

        if self.toolButtonStyle() == Qt.ToolButtonIconOnly:
            # Contracted state
            if self.orientation() == Qt.Vertical:
                self._toggle_btn.setArrowType(Qt.RightArrow)
            else:
                self._toggle_btn.setArrowType(Qt.DownArrow)
        else:
            # Expanded state
            if self.orientation() == Qt.Vertical:
                self._toggle_btn.setArrowType(Qt.LeftArrow)
            else:
                self._toggle_btn.setArrowType(Qt.UpArrow)

    def on_toggle_clicked(self, checked: bool):
        """Handle toggle button click to expand or contract the toolbar."""
        if checked:
            self.expand_me()
        else:
            self.contract_me()

    def expand_me(self):
        """Expand the toolbar."""
        if self.orientation() == Qt.Vertical:
            tool_style = Qt.ToolButtonTextBesideIcon
            align = Qt.AlignLeft | Qt.AlignVCenter
        else:  # Qt.Horizontal
            tool_style = Qt.ToolButtonTextUnderIcon
            align = Qt.AlignHCenter | Qt.AlignTop

        # show icons and text
        self.setToolButtonStyle(tool_style)

        # update toggle button visual state
        self._sync_toggle_state(True)
        self.update_arrow_icon()

        # align icons and text
        layout = self.layout()
        layout.setSpacing(layout.spacing())
        for i in range(layout.count()):
            tool = layout.itemAt(i)
            if tool:
                widget = tool.widget()
                if widget is getattr(self, "_spacer", None):
                    continue
                if widget is getattr(self, "_toggle_btn", None):
                    widget.setToolButtonStyle(Qt.ToolButtonIconOnly)
                    if self.orientation() == Qt.Vertical:
                        widget.setSizePolicy(
                            QSizePolicy.Expanding, QSizePolicy.Preferred
                        )
                        tool.setAlignment(Qt.AlignBottom)
                    else:
                        widget.setSizePolicy(
                            QSizePolicy.Preferred, QSizePolicy.Expanding
                        )
                        tool.setAlignment(Qt.AlignRight)
                    continue
                tool.setAlignment(align)
            # https://doc.qt.io/qt-5/qlayoutitem.html#setAlignment

    def contract_me(self):
        """Contract the toolbar."""
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self._sync_toggle_state(False)
        self.update_arrow_icon()
