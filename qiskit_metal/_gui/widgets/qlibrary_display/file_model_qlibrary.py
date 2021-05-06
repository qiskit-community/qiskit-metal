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

from PySide2.QtGui import QFont
from PySide2.QtCore import QFileSystemWatcher, Qt, Signal, QModelIndex
from PySide2.QtWidgets import QFileSystemModel, QWidget


class QFileSystemLibraryModel(QFileSystemModel):
    """
    File System Model for displaying QLibrary in MetalGUI
    Has additional FileWatcher added to keep track of edited
    QComponent files and, in developer mode,
    to alert the view/delegate to let the user know these files
    are dirty and refresh the design
    """
    FILENAME = 0  # Column index to display filenames
    REBUILD = 1  # Column index to display Rebuild button

    file_dirtied_signal = Signal()
    file_cleaned_signal = Signal()

    def __init__(self, parent: QWidget = None):
        """
        Initializes Model


        Args:
            parent(QWidget): Parent widget
        """
        super().__init__(parent)

        self.file_system_watcher = QFileSystemWatcher()
        self.dirtied_files = {}
        self.ignored_substrings = {'.cpython', '__pycache__'}
        self.is_dev_mode = False
        self.columns = ['QComponents', 'Rebuild Buttons']

    def is_valid_file(self, file: str)->bool:
        """
        Whether it's a file the FileWatcher should track
        Args:
            file: Filename

        Returns:
            bool: Whether file is one the FileWatcher should track

        """
        for sub in self.ignored_substrings:
            if sub in file:
                return False
        return True

    def clean_file(self, filepath: str):
        """
        Remove file from the dirtied_files dictionary
        and remove any parent files who are only dirty due to
        this file. Emits file_cleaned_signal.
        Args:
            filepath: Clean file path

        """
        filename = self.filepath_to_filename(filepath)
        self.dirtied_files.pop(filename, f"failed to pop {filepath}")

        sep = os.sep if os.sep in filepath else '/'
        for file in filepath.split(sep):
            if file in self.dirtied_files:
                # if file was in dirtied files only because it is a parent dir
                # of filename, remove
                self.dirtied_files[file].discard(filename)

                if len(self.dirtied_files[file]) < 1:
                    self.dirtied_files.pop(file)
        self.file_cleaned_signal.emit()

    def dirty_file(self, filepath: str):
        """
        Adds file and parent directories to the dirtied_files dictionary.
        Emits file_dirtied_signal
        Args:
            filepath: Dirty file path

        """
        filename = self.filepath_to_filename(filepath)
        if not self.is_valid_file(filename):
            return

        sep = os.sep if os.sep in filepath else '/'
        for file in filepath.split(sep):

            if file in self.dirtied_files:
                self.dirtied_files[file].add(filename)
            else:
                self.dirtied_files[file] = {filename}

        # overwrite filename entry from above
        self.dirtied_files[filename] = {filepath}

        self.file_dirtied_signal.emit()

    def is_file_dirty(self, filepath: str) -> bool:
        """
        Checks whether file is dirty
        Args:
            filepath: File in question

        Returns:
            bool: Whether file is dirty

        """
        filename = self.filepath_to_filename(filepath)
        return filename in self.dirtied_files

    def filepath_to_filename(self, filepath: str) -> str:  # pylint: disable=R0201, no-self-use
        """
        Gets just the filename from the full filepath
        Args:
            filepath: Full file path

        Returns:
            str: Filename

        """

        # split on os.sep and / because PySide appears to sometimes use / on
        # certain Windows
        filename = filepath.split(os.sep)[-1].split('/')[-1]
        if '.py' in filename:
            return filename[:-len('.py')]
        return filename

    def setRootPath(self, path: str) -> QModelIndex:
        """
        Sets FileWatcher on root path and adds rootpath to model
        Args:
            path: Root path

        Returns:
            QModelIndex: Root index

        """

        for root, _, files in os.walk(path):
            # do NOT use directory changed -- fails for some reason
            for name in files:
                self.file_system_watcher.addPath(os.path.join(root, name))

        self.file_system_watcher.fileChanged.connect(self.alert_highlight_row)

        return super().setRootPath(path)

    def alert_highlight_row(self, filepath: str):
        """
        Dirties file and re-adds edited file to the FileWatcher
        Args:
            filepath: Dirty file


        """
        # ensure get only filename
        if filepath not in self.file_system_watcher.files():
            if os.path.exists(filepath):
                self.file_system_watcher.addPath(filepath)
        self.dirty_file(filepath)

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = ...) -> typing.Any:
        """ Set the headers to be displayed.

        Args:
            section (int): Section number
            orientation (Qt orientation): Section orientation
            role (Qt display role): Display role.  Defaults to DisplayRole.

        Returns:
            typing.Any: The header data, or None if not found
        """

        if role == Qt.DisplayRole:
            if not self.is_dev_mode and section == self.REBUILD:
                return ""

            if orientation == Qt.Horizontal:
                if section < len(self.columns):
                    return self.columns[section]

        elif role == Qt.FontRole:
            if section == 0:
                font = QFont()
                font.setBold(True)
                return font

        return super().headerData(section, orientation, role)

    def set_file_is_dev_mode(self, ison: bool):
        """
        Set dev_mode
        Args:
            ison: Whther dev_mode is on

        """
        self.is_dev_mode = ison
