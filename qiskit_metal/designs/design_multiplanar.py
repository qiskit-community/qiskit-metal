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
"""Module containing Multi-Planar design for CPW type
geometry. Supports tek file approach for layer stack definitions."""

#from typing import Tuple

from qiskit_metal.designs.design_base import QDesign
from qiskit_metal.toolbox_metal.layer_stack_handler import LayerStackHandler
from addict import Dict

__all__ = ['DesignMulti']


class MultiPlanar(QDesign):
    """Metal class for a multiple planar design, consisting of either single or multiple chips.
    Typically assumed to have some CPW geometries.

    Inherits QDesign class.
    """

    def __init__(self,
                 metadata: dict = None,
                 overwrite_enabled: bool = False,
                 enable_renderers: bool = True,
                 layer_stack_filename: str = None):
        """Pass metadata to QDesign.

        Args:
            metadata (dict, optional): Pass to QDesign. Defaults to {}.
            overwrite_enabled (bool, optional): Passed to QDesign base class. Defaults to False.
            enable_renderers (bool, optional): Passed to QDesign base class. Defaults to True.
        """

        super().__init__(metadata=metadata,
                         overwrite_enabled=overwrite_enabled,
                         enable_renderers=enable_renderers)

        #just using the single planar approach for the moment
        #still have the different chips, or just all via layers?
        self._add_chip_info()

        #generates the table for the layer information
        self.ls_filename = layer_stack_filename

        # Note: layers numbers can be repeated since there can be datatypes.
        self.ls = self._add_layer_stack()

        self._uwave_package = Dict()
        self._populate_uwave_values()

    def _populate_uwave_values(self):
        """Can be updated by user.
        """
        self._uwave_package[
            'sample_holder_top'] = '890um',  # how tall is the vacuum above center_z
        self._uwave_package[
            'sample_holder_bottom'] = '1650um'  # how tall is the vacuum below z=0

    def _add_layer_stack(self) -> LayerStackHandler:
        """Adds the data structure for the "layer_stack file" in the design for defining
        the layer stack. Simple initial layer is generated (to support the default
        layer used in all components).
        """
        return LayerStackHandler(self)

    def _add_chip_info(self):
        """Used to determine size of fill box by either 'size' data or box_plus_buffer.

        GDSPY is using numbers based on 1 meter unit.
        When the gds file is exported, data is converted to "user-selected" units.
        centered at (0,0) and 9 by 6 size.

        NOTE: self._chips dict comes from QDesign base class.
        """
        self._chips['main'] = Dict()

        self._chips['main']['size'] = Dict(
            center_x='0.0mm',
            center_y='0.0mm',
            size_x='9mm',
            size_y='7mm',
        )
