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

import os
import typing
from pathlib import Path
from PySide2.QtCore import QModelIndex, QTimeZone, Qt, QSize
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QFileSystemModel
from qiskit_metal._gui.utility.utils import findProperty


class QFileSystemLibraryModel(QFileSystemModel):
    """
    File System Model for displaying QLibrary in MetalGUI

    """
    path_imgs = None  # type: Path
    FILENAME = 0
    imageCache = dict()
    nameCache = dict()
    defaultFilename = None
    size = 64

    def __init__(self, path_imgs):
        super().__init__()
        self.path_imgs = path_imgs
        self.defaultFilename = str(path_imgs / "metal_logo.png")
        pixmap = QPixmap(self.defaultFilename).scaled(
            QSize(self.size, self.size), Qt.KeepAspectRatio,
            Qt.SmoothTransformation)
        self.imageCache[self.defaultFilename] = pixmap

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

        # There are multiple columns so we don't want display an
        # image in each one, (see filterAcceptsColumn)
        if index.column() == 0:
            if not self.isDir(index):
                qfileinfo = self.fileInfo(index)
                absoluteFilename = str(qfileinfo.absoluteFilePath())
                if role == Qt.DecorationRole:
                    matches = findProperty(absoluteFilename,
                                           "\.\. image::[\r\n]+([^\r\n]+)")
                    if matches is not None and len(matches) != 0:
                        iconfile = matches[0].lstrip()
                        pathFilename = self.path_imgs / "components" / iconfile
                        if pathFilename.is_file():
                            stringFilename = str(pathFilename)
                            # imageCache pixmaps as they are seen
                            if stringFilename in self.imageCache:
                                return self.imageCache[stringFilename]
                            else:
                                pixmap = QPixmap(stringFilename).scaled(
                                    QSize(self.size, self.size),
                                    Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                self.imageCache[stringFilename] = pixmap
                                return pixmap
                    # display default image
                    return self.imageCache[self.defaultFilename]
                elif role == Qt.DisplayRole:
                    relativeFilename = qfileinfo.fileName()
                    if relativeFilename in self.nameCache:
                        return self.nameCache[relativeFilename]
                    else:
                        matches = findProperty(absoluteFilename,
                                               "\.\. meta::[\r\n]+([^\r\n]+)")
                        if matches is not None and len(matches) != 0:
                            displayName = matches[0].lstrip()
                            self.nameCache[relativeFilename] = displayName
                            return displayName
                        else:
                            return relativeFilename
            else:
                if role == Qt.SizeHintRole:
                    return QSize(10, 25)

        return super().data(index, role)
