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
File System Model for QLibrary Display
"""

import typing
from pathlib import Path
from PySide2.QtCore import QModelIndex, QTimeZone, Qt, QSize
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QFileSystemModel


class QFileSystemLibraryModel(QFileSystemModel):
    """
    File System Model for displaying QLibrary in MetalGUI

    """
    path_imgs = None  # type: Path
    FILENAME = 0
    CACHE = dict()

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
        size = 64
        if not self.isDir(index):
            if role == Qt.DecorationRole:
                qfileinfo = self.fileInfo(index)
                iconfile = qfileinfo.fileName().replace(".py", ".png")
                pathFilename = self.path_imgs / "components" / iconfile

                if pathFilename.is_file():
                    stringFilename = str(pathFilename)
                    # cache pixmaps as they are seen
                    if stringFilename in self.CACHE:
                        return self.CACHE[stringFilename]
                    else:
                        pixmap = QPixmap(stringFilename).scaled(
                            QSize(size, size), Qt.KeepAspectRatio,
                            Qt.SmoothTransformation)
                        self.CACHE[stringFilename] = pixmap
                        return pixmap

        return super().data(index, role)