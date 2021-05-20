from qiskit_metal._gui.main_window.main_window_modes.developer_mode import DevModeMainWindow
from qiskit_metal._gui.main_window.main_window_modes.user_mode.main_window_user_mode import UserModeMainWindow

from PySide2.QtWidgets import QWidget

# Ryan Where do designs go?

class MainWindowController(QWidget):
  def __init__(self, backend):
    self.modes = [DevModeMainWindow, UserModeMainWindow]
    self.backend = backend

  def set_main_window(self, mode, *args, **kwargs):
    self.current_window = mode(self, self.backend)



