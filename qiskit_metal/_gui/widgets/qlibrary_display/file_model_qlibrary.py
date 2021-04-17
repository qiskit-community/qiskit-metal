import importlib
import importlib.util
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List, TYPE_CHECKING

from PySide2.QtGui import QFont
from PySide2.QtCore import Qt, QTimer, QModelIndex, QFileSystemWatcher, Signal
from PySide2.QtWidgets import (
    QFileSystemModel, QErrorMessage)

import PySide2
import typing


class QFileSystemLibraryModel(QFileSystemModel):
    """
    File System Model for displaying QLibrary in MetalGUI
    Has additional FileWatcher added to keep track of edited QComponent files and, in developer mode,
    to alert the view/delegate to let the user know these files are dirty and refresh the design
    """
    FILENAME = 0  # Column index to display filenames
    REBUILD = 1  # Column index to display Rebuild button

    file_dirtied_signal = Signal()
    file_cleaned_signal = Signal()

    def __init__(self, *args):
        """
        Initializes Model

        is_dev_mode -- Whether the MetalGUI is in Developer Mode or not

        Args:
            *args:
        """
        super().__init__(*args)

        self.file_system_watcher = QFileSystemWatcher()
        self.dirtied_files = {}
        self.ignored_substrings = {'.cpython', '__pycache__'}
        self.is_dev_mode = False
        self.columns = ['QComponents', 'Rebuild Buttons']

    def is_valid_file(self, file: str):
        """
        Whether it's a file the FileWatcher should track
        Args:
            file: Filename

        Returns:

        """
        for sub in self.ignored_substrings:
            if sub in file:
                return False
        return True

    def clean_file(self, filepath: str):
        """
        Remove file from the dirtied_files dictionary and remove any parent files who are only dirty due to
        this file
        Args:
            filepath: Clean file path

        """
        filename = self.filepath_to_filename(filepath)
        self.dirtied_files.pop(filename, f"failed to pop {filepath}")

        sep = os.sep if os.sep in filepath else '/'
        for file in filepath.split(sep):
            if file in self.dirtied_files:
                # if file was in dirtied files only because it is a parent dir of filename, remove
                self.dirtied_files[file].discard(filename)

                if len(self.dirtied_files[file]) < 1:
                    self.dirtied_files.pop(file)
        self.file_cleaned_signal.emit()

    def dirty_file(self, filepath: str):
        """
        Adds file and parent directories to the dirtied_files dictionary
        Args:
            filepath: Dirty file path

        Returns:

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

        Returns: Whether file is dirty

        """
        filename = self.filepath_to_filename(filepath)
        return filename in self.dirtied_files

    def filepath_to_filename(self, filepath: str) -> str:
        """
        Gets just the filename from the full filepath
        Args:
            filepath: Full file path

        Returns: Filename

        """

        # split on os.sep and / because PySide appears to sometimes use / on certain Windows
        filename = filepath.split(os.sep)[-1].split('/')[-1]
        if '.py' in filename:
            return filename[:-len('.py')]
        return filename

    def setRootPath(self, path: str) -> PySide2.QtCore.QModelIndex:
        """
        Sets FileWatcher on root path and adds rootpath to model
        Args:
            path: Root path

        Returns: Root index

        """

        for root, dirs, files in os.walk(path):
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

    def headerData(self, section: int, orientation: PySide2.QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        """ Set the headers to be displayed.

        Args:
            section (int): Section number
            orientation (Qt orientation): Section orientation
            role (Qt display role): Display role.  Defaults to DisplayRole.

        Returns:
            str: The header data, or None if not found
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

    def set_file_is_dev_mode(self, ison: bool):
        """
        Set dev_mode
        Args:
            ison: Whther dev_mode is on

        """
        self.is_dev_mode = ison
