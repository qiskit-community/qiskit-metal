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
    FILENAME = 0
    REBUILD = 1

    file_dirtied_signal = Signal()
    file_cleaned_signal = Signal()

    def __init__(self, *args):
        super().__init__(*args)

        self.file_system_watcher = QFileSystemWatcher()
        self.dirtied_files = {}
        self.ignored_substrings = {'.cpython', '__pycache__'}
        self.is_dev_mode = False
        self.columns = ['QComponents', 'Rebuild Buttons']


        #all the columns on a row

    def is_valid_file(self, file):
        for sub in self.ignored_substrings:
            if sub in file:
                return False
        return True

    def clean_file(self, filepath):
        print("cleaning file: ", filepath)
        filename = self.filepath_to_filename(filepath)
        popped = self.dirtied_files.pop(filename, f"failed to pop {filepath}")

        print(f"popped = {popped}")

        sep = os.sep if os.sep in filepath else '/'
        for file in filepath.split(sep):
            if file in self.dirtied_files:
                # if file was in dirtied files only because it is a parent dir of filename, remove
                print(f"cleaning {file} which has {self.dirtied_files[file]} using {filename}")
                self.dirtied_files[file].discard(filename)
                print(f"len of {self.dirtied_files[file]} is: {len(self.dirtied_files[file])}")
                print(f"is {filename} in {self.dirtied_files[file]}: {filename in self.dirtied_files[file]}")

                if len(self.dirtied_files[file]) < 1:
                    self.dirtied_files.pop(file)
        print("dirty files now: ", self.dirtied_files)
        self.file_cleaned_signal.emit()


    def dirty_file(self, filepath):
        filename = self.filepath_to_filename(filepath)
        if not self.is_valid_file(filename):
            return

        sep = os.sep if os.sep in filepath else '/'
        for file in filepath.split(sep):

            if file in self.dirtied_files:
                self.dirtied_files[file].add(filename)
            else:
                self.dirtied_files[file] = {filename}

        self.dirtied_files[filename] = {filepath} #overwrite filename entry from above

        self.file_dirtied_signal.emit()



    def is_file_dirty(self, filepath):
        filename = self.filepath_to_filename(filepath)
        return filename in self.dirtied_files


    def filepath_to_filename(self, filepath):

        # split on os.sep and / because PySide appears to sometimes use / on certain Windows
        filename = filepath.split(os.sep)[-1].split('/')[-1]
        if '.py' in filename:
            return filename[:-len('.py')]
        return filename

    def setRootPath(self, path:str) -> PySide2.QtCore.QModelIndex:
        # watches only files - no dirs

        #print(f"is watching path: {path}: {self.file_system_watcher.addPath(path)}")
        for root, dirs, files in os.walk(path):
            #print(f"tup: root: {root.split('/')[-1]}\n                dirs: {dirs}, files: {files}")
            # do NOT use directory changed -- fails for some reason
            for name in files:
                self.file_system_watcher.addPath(os.path.join(root, name))

        self.file_system_watcher.fileChanged.connect(print)
        self.file_system_watcher.fileChanged.connect(self.alert_highlight_row)
        #print(self.file_system_watcher.files())

        return super().setRootPath(path)


    def alert_highlight_row(self, filepath:str):
        # ensure get only filename
        if filepath not in self.file_system_watcher.files():
            if os.path.exists(filepath):
                print("exists so still watching")
                self.file_system_watcher.addPath(filepath)
        self.dirty_file(filepath)


    def headerData(self, section:int, orientation:PySide2.QtCore.Qt.Orientation, role:int=...) -> typing.Any:
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
                    # print(self.columns[section])
                    return self.columns[section]

        elif role == Qt.FontRole:
            if section == 0:
                font = QFont()
                font.setBold(True)
                return font


    def set_file_is_dev_mode(self, ison:bool):
        self.is_dev_mode = ison