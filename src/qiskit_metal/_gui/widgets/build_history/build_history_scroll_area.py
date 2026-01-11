from PySide6.QtWidgets import (QLabel, QScrollArea, QVBoxLayout, QLabel,
                               QGroupBox)
from typing import List
from qiskit_metal._gui.widgets.build_history.build_history_scroll_area_ui import Ui_BuildHistory


class BuildHistoryScrollArea(QScrollArea, Ui_BuildHistory):
    """Widget for holding & displaying build logs of the component.

    This class extends the `QScrollArea` class
    """

    def __init__(self,
                 previous_builds: List[str],
                 parent=None,
                 *args,
                 **kwargs):
        """
        Args:
            previous_builds (List[str]):
                List of all previous attempted builds of the components
                (including successes and failures). Each attempted
                build is a string that will be displayed in this window.
                Assumes  previous_builds[0] is the latest log. For example. ['10PM error', '2PM error', '10AM error' ...]
                BuildHistoryScrollArea should always display the latest logs at the top
            parent (QWidget):
                Parent widget if necessary

        """
        super(BuildHistoryScrollArea, self).__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self._previous_builds = previous_builds
        self._display_logs()

    def _display_logs(self):
        """Create UI for BuildHistoryScrollAreas."""
        for build_log_indx in range(len(self._previous_builds)):
            label = QLabel(self._previous_builds[build_log_indx])
            if 'ERROR' in self._previous_builds[build_log_indx]:
                label.setStyleSheet('color: red')
            self.build_display_vertical_layout.addWidget(label)
        self.adjustSize()
        self.show()
