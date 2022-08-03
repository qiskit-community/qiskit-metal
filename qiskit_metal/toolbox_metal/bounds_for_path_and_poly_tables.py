# -*- coding: utf-8 -*-
from typing import List, Tuple, Union

from qiskit_metal.toolbox_python.utility_functions import determine_larger_box

import pandas as pd


class BoundsForPathAndPolyTables():
    """Create class which can be used by multiple renderers.  In particular, this class
    assumes a LayerStack is being used within QDesign.
    """

    def __init__(self, design: "MultiPlanar"):
        self.design = design
        self.chip_names_matched = None  # bool
        self.valid_chip_names = None  # set of valid chip names from layer_stack

    def get_bounds_of_path_and_poly_tables(
        self, box_plus_buffer: bool, qcomp_ids: List, case: int, x_buff: float,
        y_buff: float
    ) -> tuple[tuple[float, float, float, float], pd.DataFrame, bool, Union[
            None, set]]:
        """If box_plus_buffer is True, returns a tuple containing minx, miny, maxx, maxy values for the
        bounds of what was selected to be rendered.
        Else, use the chip size for Tuple.

        Also, return the Tuple within the class to can be used later within a renderer.

        Args:
            box_plus_buffer (bool): Use the box of selected components plus a buffer size OR
                                the chip size based on QComponents selected.
            qcomp_ids (List):  Empty or partial list of components in QDesign. From QRenderer.get_unique_component_ids
            case (int): Return code used from QRenderer.get_unique_component_ids()
            x_buff (float): If box_plus_buffer, need the buffer value in x coordinate.
            y_buff (float): If box_plus_buffer, need the buffer value in y coordinate.

        Returns:
            tuple[tuple[float, float, float, float], pd.DataFrame, bool, Union[None,set]]:
                                    tuple: minx, miny, maxx, maxy values based
                                                    on either total chip size or box_plus_buffer.
                                    pd.DataFrame: The path and poly dataframes concatenated for qcomp_ids
                                    bool: If there is a key in design with same chip_name as in layer_stack
                                    Union[None,set]: Either None if the names don't match,
                                                    or the set of chip_names that can be used.
        """
        box_for_ansys = None
        self.chip_names_matched = None
        self.valid_chip_names = None

        path_dataframe = self.design.qgeometry.tables['path']
        poly_dataframe = self.design.qgeometry.tables['poly']

        if box_plus_buffer:
            # Based on component selection, determine the bounds for box_plus_buffer.
            frames = None
            path_and_poly_with_valid_comps = None

            if case == 2:  # One or more components not in QDesign.
                self.design.logger.warning("One or more components not found.")
            elif case == 1:  # Render all components
                frames = [path_dataframe, poly_dataframe]
            else:  # Strict subset rendered.
                mask_path = path_dataframe['component'].isin(qcomp_ids)
                mask_poly = poly_dataframe['component'].isin(qcomp_ids)
                subset_path_df = path_dataframe[mask_path]
                subset_poly_df = poly_dataframe[mask_poly]
                frames = [subset_path_df, subset_poly_df]

            #Concat the frames and then determine the total bounds of all the geometries.
            # maybe, change name to package_cavity
            path_and_poly_with_valid_comps = pd.concat(frames,
                                                       ignore_index=True)
            minx, miny, maxx, maxy = list(
                path_and_poly_with_valid_comps['geometry'].total_bounds)
            # minx, miny, maxx, maxy = list(
            #     pd.concat(frames, ignore_index=True)['geometry'].total_bounds)
            # # Add the buffer, using options for renderer.
            # x_buff = parse_entry(self._options["x_buffer_width_mm"])
            # y_buff = parse_entry(self._options["y_buffer_width_mm"])

            minx -= x_buff
            miny -= y_buff
            maxx += x_buff
            maxy += y_buff
            box_for_ansys = (minx, miny, maxx, maxy)
            return box_for_ansys, path_and_poly_with_valid_comps, self.chip_names_matched, self.valid_chip_names
        else:  # Incorporate all the chip sizes.

            minx, miny, maxx, maxy = self.get_box_for_ansys()
            box_for_ansys = (minx, miny, maxx, maxy)

            frames = [path_dataframe, poly_dataframe]
            path_and_poly_with_valid_comps = pd.concat(frames,
                                                       ignore_index=True)
            return box_for_ansys, path_and_poly_with_valid_comps, self.chip_names_matched, self.valid_chip_names

    def get_box_for_ansys(
            self
    ) -> Union[None, Union[Tuple[float, float, float, float], None]]:
        """Assuming the chip size is used from Multiplanar design, and list of chip_names
        comes from layer_stack that will be used to determine the box size for simulation.

        Returns:
            Union[None, Union[Tuple[float, float, float, float], None]]:
                                None if not able to get the chip information
                                Tuple holds the box to use for simulation [minx, miny, maxx, maxy]
        """

        self.chip_names_matched, self.valid_chip_names = self.are_all_chipnames_in_design(
        )

        minx, miny, maxx, maxy = None, None, None, None
        if self.chip_names_matched:
            # Using the chip size from Multiplanar design and z_coord from layer_stack, get the box
            # for chip_name in self.chip_names_matched:
            for chip_name in self.valid_chip_names:
                if self.design.chips[chip_name]['size']:
                    chip_box, return_code = self.get_x_y_for_chip(chip_name)

                    if return_code == 0:  # All was found and good.
                        minx, miny, maxx, maxy = determine_larger_box(
                            minx, miny, maxx, maxy, chip_box)

                else:
                    self.chip_size_not_in_chipname_within_design(chip_name)

        return minx, miny, maxx, maxy

    def are_all_chipnames_in_design(self) -> Tuple[bool, Union[set, None]]:
        """Using chip names in layer_stack information,
        then check if the information is in MultiPlanar design.

        Returns:
            Tuple[bool, Union[set, None]]: bool if there is a key in design with same chip_name as in layer_stack
                                        Union has either None if the names don't match,
                                        or the set of chip_names that can be used.
        """

        chip_set_from_design = set(self.design.chips.keys())
        chip_set_from_layer_stack = self.design.ls.get_unique_chip_names()
        if not chip_set_from_layer_stack.issubset(chip_set_from_design):
            self.chip_names_not_in_design(chip_set_from_layer_stack,
                                          chip_set_from_design)
            return False, None

        return True, chip_set_from_layer_stack

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

        if chip_name in self.design.chips:
            if 'size' in self.design.chips[chip_name]:

                size = self.design.parse_value(
                    self.design.chips[chip_name]['size'])
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

                    self.design.logger.warning(
                        f'Size information within self.design.chips[{chip_name}][\"size\"]'
                        f' is NOT an int or float.')
                    return x_y_location, 2

                self.design.logger.warning(
                    'center_x or center_y or size_x or size_y '
                    f' NOT in self.design.chips[{chip_name}][\"size\"]')
                return x_y_location, 2

            self.design.logger.warning(
                f'Information for size in NOT in self.design.chips[{chip_name}]'
                ' dict. Return "None" in tuple.')
            return x_y_location, 2

        self.design.logger.warning(
            f'Chip name "{chip_name}" is not in self.design.chips dict. Return "None" in tuple.'
        )
        return x_y_location, 1


######### Warnings and Errors##################################################

    def chip_names_not_in_design(self, layer_stack_names: set,
                                 design_names: set):
        """
        Tell user to check the chip name and data in design.

        Args:
            layer_stack_names (set): Chip names from layer_stack.
            design_names (set): Chip names from design.
        """
        self.design.logger.warning(
            f'\nThe chip_names from layer_stack are not in design. '
            f'\n The names in layer_stack:{layer_stack_names}.'
            f'\n The names in design:{design_names}.')

    def chip_size_not_in_chipname_within_design(self, chip_name: str):
        """
        Tell user to check the chip size data within design.

        Args:
            chip_name (str): Chip names from layer_stack.
        """
        self.design.logger.error(
            f'\nThe chip_name:{chip_name} within design. '
            f'\n Update your QDesign or subclass to see confirm the size information is provided.'
        )