# -*- coding: utf-8 -*-

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
"""
Proxy Model to clean display of QComponents in Library tab
"""
from PySide2.QtCore import QModelIndex, QSortFilterProxyModel, Qt
import typing

class LibraryFileProxyModel(QSortFilterProxyModel):

    def __init__(self, *args, **kwargs):
        """Proxy Model for cleaning up Directory Model for displaying GUI's QLibrary """

        super().__init__(*args, **kwargs)
        # finds all files that
        # (Aren't hidden (begin w/ .), don't begin with __init__, don't begin with _template, etc. AND end in .py)  OR (don't begin with __pycache__ and don't have a '.' in the name
        # (QComponent files) OR (Directories)
        self.accepted_files__regex = r"(^((?!\.))(?!__init__)(?!_template)(?!__pycache__).*\.py)|(?!__pycache__)(?!base)(^([^.]+)$)"
        self.setFilterRegExp(self.accepted_files__regex)
        self.is_dev_mode = False


    def set_dev_mode(self, ison:bool):
        self.is_dev_mode = ison

    def filterAcceptsColumn(self, source_column: int,
                            source_parent: QModelIndex) -> bool:
        """Filters out unwanted file information in display"""
        if (self.is_dev_mode and source_column <= self.sourceModel().REBUILD):
            return True
        elif source_column <= self.sourceModel().REBUILD:  # Won't show Size, Kind, Date Modified, etc. for QFileSystemModel
            return True

        return False



    def data(self, index:QModelIndex, role:int = Qt.DisplayRole) -> typing.Any:
        from PySide2.QtCore import Qt,QSize

        if role == Qt.EditRole:
            return self.data(index, Qt.DisplayRole)

        elif role == Qt.SizeHintRole:
            return QSize(10,25)

        elif role == Qt.DisplayRole and index.column() == 1:
            return ""

        else:
            return super().data(index, role)


