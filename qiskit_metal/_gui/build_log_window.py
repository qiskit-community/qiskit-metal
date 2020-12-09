from PySide2.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QLabel,
    QGroupBox
)
from typing import List


class ComponentBuildLogWindow(QScrollArea):
    def __init__(self, previous_builds: List[str], reversedlogs=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_builds = previous_builds
        self._title = "Previous Builds"
        self.reversed = reversedlogs
        self._initUi()


    def _initUi(self):
        self.setWindowTitle(self._title)
        form_layout = QVBoxLayout()


        if self.reversed:
            for build_log_indx in range(len(self._previous_builds), -1, -1):
                label = QLabel(self._previous_builds[build_log_indx])
                form_layout.addWidget(label)
        else:
            for build_log_indx in range(len(self._previous_builds)):
                label = QLabel(self._previous_builds[build_log_indx])
                form_layout.addWidget(label)

        group_box = QGroupBox("")
        group_box.setLayout(form_layout)

        self.setWidget(group_box)
        self.setWidgetResizable(True)

        self.adjustSize()