from pyqode.core.panels.folding import FoldingPanel
from pyqode.core.api.folding import FoldScope
from pyqode.core.api import TextBlockHelper, folding, TextDecoration, \
    DelayJobRunner
from pyqode.qt import QtCore, QtWidgets, QtGui, PYQT5_API
from qiskit_metal.toolbox_metal.exceptions import IncorrectQtException
import os


class MetalPyqodeFoldingPanel(FoldingPanel):
    """Hacky, temporary solutions to PyQode.core.panels.FoldingPanel not
    calling the correct function when PySide2 is being used.

    The _draw_fold_indicator threw:
    AttributeError: module 'pyqode.qt.QtGui' has no attribute 'QStyleOptionViewItemV2'
    when opt = QtGui.QStyleOptionViewItemV2() was called.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _draw_fold_indicator(self, top, mouse_over, collapsed, painter):
        """Draw the fold indicator/trigger (arrow).

        Args:
            top (int): Top position
            mouse_over (bool): Whether the mouse is over the indicator
            collapsed (bool): Whether the trigger is collapsed or not.
            painter (PySide.QtGui.QPainter): QPainter
        """
        rect = QtCore.QRect(0, top,
                            self.sizeHint().width(),
                            self.sizeHint().height())
        self._native = False
        index = 0
        if not collapsed:
            index = 2
        if mouse_over:
            index += 1
        QtGui.QIcon(self._custom_indicators[index]).paint(painter, rect)
