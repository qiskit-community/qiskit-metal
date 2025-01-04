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

# The code is modified from DesignPlanar to implement flipchip-compatible QDesign class. (SK/Chalmers/20210610)
"""Module containing Basic Qiskit Metal FlipChip design for CPW type
geometry."""

# from typing import TYPE_CHECKING
from typing import Tuple

# from typing import Dict as Dict_
# from typing import List, Union

from .design_base import QDesign, Dict

__all__ = ["DesignFlipChip"]


class DesignFlipChip(QDesign):
    """Metal class for a flipchip design, consisting of two chips with their device sides facing each other.
    Typically assumed to have some CPW geometries.

    Inherits QDesign class.
    """

    def __init__(
        self,
        metadata: dict = None,
        overwrite_enabled: bool = False,
        enable_renderers: bool = True,
    ):
        """Pass metadata to QDesign.

        Args:
            metadata (dict, optional): Pass to QDesign. Defaults to {}.
            overwrite_enabled (bool, optional): Passed to QDesign base class. Defaults to False.
            enable_renderers (bool, optional): Passed to QDesign base class. Defaults to True.
        """

        super().__init__(
            metadata=metadata,
            overwrite_enabled=overwrite_enabled,
            enable_renderers=enable_renderers,
        )
        self.variables[
            "sample_holder_top"] = "890um"  # how tall is the vacuum above z=0
        self.variables[
            "sample_holder_bottom"] = "1650um"  # how tall is the vacuum below z=0
        self.add_chip_info()

    def add_chip_info(self):
        """TODO How to get the values into self.chip. Will need to set up
        parser for "self.p" for design base. For now, just hard code in
        something.

        # GDSPY is using numbers based on 1 meter unit.
        # When the gds file is exported, data is converted to "user-selected" units.
        # centered at (0,0) and 9 by 6 size.

        NOTE: self._chips dict comes from QDesign base class.
        """
        # Reinitilise self._chips, then add two chips
        self._chips = {}
        self._chips["C_chip"] = Dict(material="silicon",
                                     layer_start="0",
                                     layer_end="2048")
        self._chips["Q_chip"] = Dict(material="silicon",
                                     layer_start="0",
                                     layer_end="2048")

        self._chips["C_chip"]["size"] = Dict(
            center_x="0.0mm",
            center_y="0.0mm",
            center_z="0.0mm",
            size_x="9mm",
            size_y="9mm",
            size_z="-280um",  # chip extends in negative z direction by 280 um
            sample_holder_top=self.variables["sample_holder_top"],
            sample_holder_bottom=self.variables["sample_holder_bottom"],
        )

        self._chips["Q_chip"]["size"] = Dict(
            center_x="0.0mm",
            center_y="0.0mm",
            center_z="20 um",
            size_x="9mm",
            size_y="9mm",
            size_z="280um",  # chip extends in positive z direction by 280 um
            sample_holder_top=self.variables["sample_holder_top"],
            sample_holder_bottom=self.variables["sample_holder_bottom"],
        )

    def get_x_y_for_chip(self, chip_name: str) -> Tuple[tuple, int]:
        """
        If the chip_name is in self.chips, along with entry for size
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
            if "size" in self._chips[chip_name]:

                size = self.parse_value(self.chips[chip_name]["size"])
                if ("center_x" in size and "center_y" in size and
                        "size_x" in size and "size_y" in size):
                    if (type(size.center_x) in [int, float] and
                            type(size.center_y) in [int, float] and
                            type(size.size_x) in [int, float] and
                            type(size.size_y) in [int, float]):
                        x_y_location = (
                            size["center_x"] - (size["size_x"] / 2.0),
                            size["center_y"] - (size["size_y"] / 2.0),
                            size["center_x"] + (size["size_x"] / 2.0),
                            size["center_y"] + (size["size_y"] / 2.0),
                        )
                        return x_y_location, 0

                    self.logger.warning(
                        f'Size information within self.chips[{chip_name}]["size"]'
                        f" is NOT an int or float.")
                    return x_y_location, 2

                self.logger.warning("center_x or center_y or size_x or size_y "
                                    f' NOT in self._chips[{chip_name}]["size"]')
                return x_y_location, 2

            self.logger.warning(
                f"Information for size in NOT in self._chips[{chip_name}]"
                ' dict. Return "None" in tuple.')
            return x_y_location, 2

        self.logger.warning(
            f'Chip name "{chip_name}" is not in self._chips dict. Return "None" in tuple.'
        )
        return x_y_location, 1
