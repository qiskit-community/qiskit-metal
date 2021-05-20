# functions
# non-generated UI edits
# QMainWindow
# setup Application
# stylesheets?

from qiskit_metal._gui.main_window.main_window_modes.user_mode.main_window_user_mode import UserModeMainWindow
from qiskit_metal._gui.main_window.main_window_modes.ModeMainWindow import ModeMainWindow
from PySide2.QtCore import QFileSystemWatcher, Qt, Signal, QModelIndex



class DevModeMainWindow():
  def __init__(self, controller, design):
    self.ui = GeneratedUI()
    self.functions = DevModeFunctions(controller, design)

  def manuallychange_GUI_layout(self):
    # Dockify things
    pass



class DevModeFunctions(ModeMainWindow):
  # from QMainWindowExtension and parts of QMainWindowBaseHandler
  change_mode = Signal(ModeMainWindow)

  def __init__(self, controller, backend):
    self.controller = controller
    self.backend = backend

  def do_rebuild(self):
    self.button.rebuild()
    pass
  def save_file(self):
    pass

  # changing windows
  def ChangeToNonUserMode(self): # Ryan how
    self.button.clicked.connect(lambda x: self.controller.set_main_window(UserModeMainWindow, x))


class GeneratedUI():
  def __init__(self):
    pass

