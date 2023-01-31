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
from typing import Tuple

__all__ = ['MultiPlanar']


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
            'sample_holder_top'] = '890um'  # how tall is the vacuum above center_z
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

    def get_x_y_for_chip(self, chip_name: str) -> Tuple[tuple, int]:
        """If the chip_name is in self.chips, along with entry for size
        information then return a tuple=(minx, miny, maxx, maxy). Used for
        subtraction while exporting design.

        Args:
            chip_name (str): Name of chip that you want the size of.

        Returns:
            Tuple[tuple, int]:
            tuple: The exact placement on rectangle coordinate (minx, miny, maxx, maxy).
            int: 0=all is good
            1=chip_name not in self._chips
            2=size information missing or no good
        """
        x_y_location = tuple()

        if chip_name in self._chips:
            if 'size' in self._chips[chip_name]:

                size = self.parse_value(self.chips[chip_name]['size'])
                if      'center_x' in size               \
                    and 'center_y' in size          \
                    and 'size_x' in size            \
                    and 'size_y' in size:
                    if type(size.center_x) in [int, float] and \
                            type(size.center_y) in [int, float] and \
                            type(size.size_x) in [int, float] and \
                            type(size.size_y) in [int, float]:
                        x_y_location = (
                            size['center_x'] - (size['size_x'] / 2.0),
                            size['center_y'] - (size['size_y'] / 2.0),
                            size['center_x'] + (size['size_x'] / 2.0),
                            size['center_y'] + (size['size_y'] / 2.0))
                        return x_y_location, 0

                    self.logger.warning(
                        f'Size information within self.chips[{chip_name}]["size"]'
                        f' is NOT an int or float.')
                    return x_y_location, 2

                self.logger.warning('center_x or center_y or size_x or size_y '
                                    f' NOT in self._chips[{chip_name}]["size"]')
                return x_y_location, 2

            self.logger.warning(
                f'Information for size in NOT in self._chips[{chip_name}]'
                ' dict. Return "None" in tuple.')
            return x_y_location, 2

        self.logger.warning(
            f'Chip name "{chip_name}" is not in self._chips dict. Return "None" in tuple.'
        )
        return x_y_location, 1
