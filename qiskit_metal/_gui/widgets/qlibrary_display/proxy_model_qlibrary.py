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
# pylint: disable=invalid-name

import typing

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QFileSystemModel, QWidget


class LibraryFileProxyModel(QSortFilterProxyModel):
    """
    Proxy Model to clean up display for QFileSystemLibraryModel
    """

    def __init__(self, parent: QWidget = None):
        """Proxy Model for cleaning up QFileSystemLibraryModel for displaying GUI's QLibrary
        Args:
            parent:(QWidget) Parent widget
        """

        super().__init__(parent)

        # finds all files that
        # (Aren't hidden (begin w/ .), don't begin with __init__, don't begin with _template, etc. AND end in .py)  OR (don't begin with __pycache__ and don't have a '.' in the name   # pylint: disable=line-too-long
        # (QComponent files) OR (Directories)
        self.accepted_files__regex = r"(^((?!\.))(?!base)(?!__init__)(?!_template)(?!_parsed)(?!__pycache__).*\.py)|(?!__pycache__)(^([^.]+)$)"  # pylint: disable=line-too-long
        self.beginResetModel()
        self.setFilterRegularExpression(self.accepted_files__regex)
        self.endResetModel()
        self.filter_text = ""

    def filterAcceptsColumn(
            self, source_column: int, source_parent: QModelIndex) -> bool:  #pylint: disable=unused-argument
        """
        Filters out unwanted file information in display
        Args:
            source_column(int): Display column in question
            source_parent(QModelIndex): Parent index
        Returns:
            bool: Whether to display column


        """
        # Won't show Size, Kind, Date Modified, etc. for QFileSystemModel
        if source_column > 0:
            return False
        return True

    def filterAcceptsRow(
            self, source_row: int, source_parent: QModelIndex) -> bool:  #pylint: disable=unused-argument
        """
        Filters out unwanted file information in display
        Args:
            source_column(int): Display column in question
            source_parent(QModelIndex): Parent index
        Returns:
            bool: Whether to display column

        """
        source_model = self.sourceModel()
        nameCache = source_model.nameCache

        index = source_model.index(source_row, 0, source_parent)
        relativeFilename = index.data(QFileSystemModel.FileNameRole)
        displayName = nameCache[
            relativeFilename] if relativeFilename in nameCache else None
        #fi = source_model.fileInfo(index)

        if displayName is not None:
            found = (self.filter_text in relativeFilename) or (self.filter_text
                                                               in displayName)
        else:
            found = self.filter_text in relativeFilename

        accept = (not relativeFilename.startswith("_")) and found
        return accept

    def data(self,
             index: QModelIndex,
             role: int = Qt.DisplayRole) -> typing.Any:
        """
        Sets standard size hint for indexes and allows
        Args:
            index(QModelIndex): Model Index holding data
            role(int): DisplayRole being requested of index
        Returns:
            Any (QVariant): Data stored under the given role for the item referred to by the index.
        """

        # allow editable
        if role == Qt.EditRole:
            self.beginResetModel()
            try:
                return self.data(index, Qt.DisplayRole)
            finally:
                self.endResetModel()

        return super().data(index, role)
