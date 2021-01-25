import sys, os
from PySide2.QtWidgets import QApplication,  QMainWindow,  QFileSystemModel, QTabWidget, QWidget
from PySide2.QtCore import  QModelIndex, QDir
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...main_window import MetalGUI


class LibraryWidget(QTabWidget):
    """
    This is just a handler (container) for the UI; it a child object of the main gui.

    This class extends the `QTabWidget` class.

    PySide2 Signal / Slots Extensions:
        The UI can call up to this class to execute button clicks for instance
        Extensions in qt designer on signals/slots are linked to this class

    **Access:**
        gui.component_window
    """

    def __init__(self, gui: MetalGUI, parent: QWidget):
        """
        Args:
            gui: (MetalGUI): the GUI
            parent (QWidget): Parent widget
        """
        super().__init__(parent)

        # Parent GUI related
        self.gui = gui
        self.logger = gui.logger
        self.statusbar_label = gui.statusbar_label


