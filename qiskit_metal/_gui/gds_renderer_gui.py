from PyQt5.QtWidgets import QMainWindow, QFileDialog
from .gds_renderer_ui import Ui_GDS_Renderer_Window

class GDSRendererWidget(QMainWindow):
    """Contains methods associated with GDS Renderer button."""

    def __init__(self, design):
        super().__init__()

        # Use UI template from Qt Designer:
        self.ui = Ui_GDS_Renderer_Window()
        self.ui.setupUi(self)

        # Access design:
        self._design = design

    @property
    def design(self):
        """Returns the design."""
        return self._design
    
    def export_file(self):
        """Exports the file."""
        filename = self.ui.lineEdit.text()
        a_gds = self.design.renderers.gds
        if filename:
            a_gds.export_to_gds(filename)
        self.close()

    def browse_files(self):
        """Browse available files in system."""
        print('Browsing files!')
