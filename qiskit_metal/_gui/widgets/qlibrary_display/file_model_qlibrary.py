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

from PySide2.QtWidgets import QFileSystemModel


class QFileSystemLibraryModel(QFileSystemModel):
    """
    File System Model for displaying QLibrary in MetalGUI

    """
    FILENAME = 0  # Column index to display filenames
    pass
