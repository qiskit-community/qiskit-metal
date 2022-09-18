# -*- coding: utf-8 -*-

from re import search
import pandas as pd
from typing import List, Tuple, Dict
from typing import Union
from addict import Dict
import os
import logging

from .parsing import TRUE_STR, FALSE_STR


class LayerStackHandler():
    """Use DataFrame to hold information for multiple chips.

    For all the chips, do NOT reuse the layer-number.  However, within the dataframe,
    we can repeat layer numbers since a layer can have multiple datatypes.

    """

    Col_Names = [
        'chip_name', 'layer', 'datatype', 'material', 'thickness', 'z_coord',
        'fill'
    ]

    def __init__(self,
                 multi_planar_design: 'MultiPlanar',
                 fname: Union['str', None] = None) -> None:
        """Use the information in MultiPlanar design to parse_value
        and get the name of filename for layer stack.

        Args:
            multi_planar_design (MultiPlanar): Class that is child of QDesign.
        """

        self.multi_planar_design = multi_planar_design
        self.logger = self.multi_planar_design.logger  # type: logging.Logger

        self.filename_csv_df = None
        if hasattr(self.multi_planar_design,
                   'ls_filename') and self.multi_planar_design.ls_filename:
            #populate pandas table from data in this file.
            self.filename_csv_df = self.multi_planar_design.ls_filename
        elif fname:
            self.filename_csv_df = fname

        self.ls_df = None
        # self.column_names = [
        #     'chip_name', 'layer', 'datatype', 'material', 'thickness',
        #     'z_coord', 'fill'
        # ]
        self.layer_stack_default = Dict(chip_name=['main', 'main'],
                                        layer=[1, 3],
                                        datatype=[0, 0],
                                        material=['pec', 'silicon'],
                                        thickness=['2um', '-750um'],
                                        z_coord=['0um', '0um'],
                                        fill=['true', 'true'])

        self._init_dataframe()
        self.is_layer_data_unique()

    def _init_dataframe(self) -> None:
        """Must check if filename for layerstack is valid before trying to import to a pandas table.
        """

        if self.filename_csv_df:
            #populate pandas table from data in this file.
            abs_path = os.path.abspath(self.filename_csv_df)
            if os.path.isfile(abs_path):
                self._read_csv_df(abs_path)
            else:
                self.logger.error(
                    f'Not able to read file.'
                    f'File:{abs_path} not read. Check the name and path.')

        else:
            #enter very basic default data for pandas table.
            self.ls_df = pd.DataFrame(data=self.layer_stack_default)

    def get_layer_datatype_when_fill_is_true(self) -> Union[dict, None]:
        """If a row has fill=True, then for each layer/datatype pair, 
        return the rest of information in the row within a dict. 

        Returns:
            Union[dict, None]: Dict with key being tuple (layer, datatype) 
                             Value is dict with key of column name of layerstack, and parsed value of column.
                         None if fill != True
        """
        if self.ls_df is None:
            abs_path = os.path.abspath(self.filename_csv_df)
            self.logger.error(
                f'Not able to read file.'
                f'File:{abs_path} not read. Check the name and path.')

        mask = self.ls_df['fill'].astype(str).str.replace(
            "[']", "", regex=True).isin(TRUE_STR)
        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:
                layer_datatype_fill = dict()
                for row in search_result_df.itertuples():
                    a_key = (row.layer, row.datatype)
                    layer_datatype_fill[a_key] = dict()
                    layer_datatype_fill[a_key]['layer'] = row.layer
                    layer_datatype_fill[a_key]['datatype'] = row.datatype
                    layer_datatype_fill[a_key][
                        'thickness'] = self.multi_planar_design.parse_value(
                            row.thickness.strip('\''))
                    layer_datatype_fill[a_key][
                        'z_coord'] = self.multi_planar_design.parse_value(
                            row.z_coord.strip('\''))
                    layer_datatype_fill[a_key]['material'] = row.material.strip(
                        '\'')
                    layer_datatype_fill[a_key][
                        'chip_name'] = row.chip_name.strip('\'')
                return layer_datatype_fill
            except Exception as ex:
                self.logger.error(
                    f'User is not using LayerStackHandler.get_layer_datatype_when_fill_is_true correctly. Check your input file.'
                    f'\nERROR:{ex}')
        return None

    def get_properties_for_layer_datatype(
            self,
            properties: List[str],
            layer_number: int,
            datatype: int = 0) -> Union[Tuple[Union[float, str, bool]], None]:
        """When user provides a layer and datatype, they can get properties
         from the layer_stack file. The allowed options for properties must
         be in Col_Names.  If any of the properties are not in Col_Names,
         None will be returned.  Otherwise a Tuple will be returned with properties
         in the same order as provided in input variable properties.

        Args:
            properties (List[str]): The column(s) within the layer stack that you want
            for a row based on layer, and datatype.
            layer_number (int): The layer number within the column denoted by layer.
            datatype (int, optional): The datatype within the column denoted
                                    by datatype. Defaults to 0.

        Returns:
            Union[Tuple[Union[float, str, bool]], None]: If the search data provided
                            in the arguments are not in the layer_stack file,
                            None will be returned.  If the search values are found in
                            layer_stack file, then a Tuple will be returned with the
                            requested properties in the same order as provided in
                            input variable denoted by properties.
        """
        if not properties:
            return None

        # Check if parameter is not a subset if Col_Names T.
        if not set(properties).issubset(set(self.Col_Names)):
            self._warning_properties(properties)
            return None

        props = Dict()
        thickness = 0.0
        z_coord = 0.0
        material = None
        fill_value = None
        chip_name = None

        if self.ls_df is None:
            abs_path = os.path.abspath(self.filename_csv_df)
            self.logger.error(
                f'Not able to read file.'
                f'File:{abs_path} not read. Check the name and path.')

        mask = (self.ls_df['layer'] == layer_number) & (self.ls_df['datatype']
                                                        == datatype)

        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:
                thickness = self.multi_planar_design.parse_value(
                    search_result_df.thickness.iloc[0].strip('\''))
                z_coord = self.multi_planar_design.parse_value(
                    search_result_df.z_coord.iloc[0].strip('\''))
                material = search_result_df.material.iloc[0].strip('\'')
                chip_name = search_result_df.chip_name.iloc[0].strip('\'')
                value = search_result_df.fill.iloc[0].strip('\'')
                if value in TRUE_STR:
                    fill_value = True
                elif value in FALSE_STR:
                    fill_value = False
                else:
                    self.logger.warning(
                        f'The \"fill\" value is neither True nor False.'
                        f'You have:{value}.  '
                        f'Will return NULL for fill value.')
                props['thickness'] = thickness
                props['z_coord'] = z_coord
                props['material'] = material
                props['fill'] = fill_value
                props['chip_name'] = chip_name
            except Exception as ex:
                self._warning_search_minus_chip(layer_number, datatype, ex)
        result = list()
        for item in properties:
            result.append(props[item])
        return tuple(result)

    def is_layer_data_unique(self) -> bool:
        """For each layer number make sure the datatypes are unique.  A layers can
        #have multiple datatypes.

        Returns:
            bool: True if empty dataframe, True if for each layer, there is ONLY one datatype. Otherwise, False.
        """
        layer_nums = self.get_unique_layer_ints()
        if layer_nums:
            for num in layer_nums:
                mask = self.ls_df['layer'] == num
                search_result_num = self.ls_df[mask]
                if not search_result_num.datatype.is_unique:
                    self.logger.warning(
                        f'There WILL BE PROBLEMS since layer {num} does not have unique datatypes.'
                    )
                    return False

        return True

    def _read_csv_df(self, abs_path: str) -> None:
        #ASSUME that self.filename_csv_df is valid file path and name.
        #https://best-excel-tutorial.com/59-tips-and-tricks/485-how-to-display-a-single-quote-in-a-cell
        try:
            self.ls_df = pd.read_csv(abs_path)

        except BaseException as error:
            self.logger.warning(
                f'Not able to create pandas dataframe.'
                f'File:{abs_path} not imported. Expected a CSV formatted file.')
            self.logger.error(f'The exception: {error}')

    def get_unique_chip_names(self) -> set:
        """Get a set of unique names used in the layer_stack dataframe.

        Returns:
            set: Unique names used in the layer stack used as either default or provided by user.
        """
        names = self.ls_df['chip_name']
        result = set(names.str.strip('\''))
        return result

    def get_unique_layer_ints(self) -> set:
        """Get a set of unique layer ints used in the layer_stack dataframe.

        Returns:
            set: Unique layer numbers used in the layer stack used as either default or provided by user.
        """
        layers = self.ls_df['layer']
        return set(layers.unique())

    def _warning_properties(self, properties: list):
        """_Give warning if the properties is

        Args:
            parameters (list): _description_
        """
        self.logger.warning(
            f'The list for properties: {properties} is not a'
            f'subset of expected column names: {self.Col_Names}')

    def _warning_search(self, chip_name: str, layer_number: int, data_type: int,
                        ex: Exception):
        """Give warning when the layerstack pandas table doesn't
        have requested chip_name, layer, and datatype information.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number.
        """

        self.logger.warning(
            f'\nERROR: {ex}'
            f'\nThere is an error searching in layer_stack dataframe using '
            f'chip_name={chip_name}, layer={layer_number}, datatype={data_type}'
        )

    def _warning_search_minus_chip(self, layer_number: int, data_type: int,
                                   ex: Exception):
        """Give warning when the layerstack pandas table doesn't
        have requested layer, and datatype information.

        Args:
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number.
        """

        self.logger.warning(
            f'\nERROR: {ex}'
            f'\nThere is an error searching in layer_stack dataframe using '
            f' layer={layer_number}, datatype={data_type}')

    def layer_stack_handler_pilot_error(self):
        """ The handler will return None if incorrect arguments are passed.
        """
        self.logger.error(
            f'User is not using LayerStackHandler.get_properties_for_chip_layer_datatype correctly.'
        )