# -*- coding: utf-8 -*-

from textwrap import fill
from xmlrpc.client import Boolean
import pandas as pd
from typing import List, Tuple
from typing import Union
from addict import Dict
import os
import logging

from .parsing import parse_units, TRUE_STR, FALSE_STR


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
        self.layer_stack_default = Dict(chip_name=['main'],
                                        layer=[1],
                                        datatype=[0],
                                        material=['pec'],
                                        thickness=['2um'],
                                        z_coord=['0um'],
                                        fill=['true'])

        self._init_dataframe()

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

    def get_properties_for_chip_layer_datatype(
            self,
            properties: List[str],
            chip_name: str,
            layer_number: int,
            datatype: int = 0) -> Union[Tuple[Union[float, str, bool]], None]:
        """When user provides a chip_name, layer and datatype, they can get properties
         from the layer_stack file. The allowed options for properties must 
         be in Col_Names.  If any of the properties are not in Col_Names, 
         None will be returned.  Otherwise a Tuple will be returned with properties 
         in the same order as provided in input variable properties. 

        Args:
            properties (List[str]): The column(s) within the layer stack that you want 
            for a row based on chip_name, layer, and datatype.
            chip_name (str): The chip name within the column denoted by chip_name.
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

        # yapf: disable
        mask = (self.ls_df['layer'] == layer_number) & 
               (self.ls_df['datatype'] == datatype) & 
               (self.ls_df['chip_name'].str.contains(chip_name))
        # yapf: enable
        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:
                thickness = self.multi_planar_design.parse_value(
                    search_result_df.thickness.iloc[0].strip('\''))
                z_coord = self.multi_planar_design.parse_value(
                    search_result_df.z_coord.iloc[0].strip('\''))          
                material = search_result_df.material.iloc[0].strip('\'')           
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
            except Exception as ex:
                self._warning_search(chip_name, layer_number, datatype, ex)
        result = tuple()
        for item in properties:
            result.append(props[item])
        return result

    def is_layer_unique(self) -> bool:
        """Check to sort on layer number make sure they are unique.
        This method is not so relevant, since layers can have datatype entries.
        Thus there can be rows with same layer number.
        """
        return self.ls_df['layer'].is_unique

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

    def get_fill_for_chip_layer_datatype(self,
                                         chip_name: str,
                                         layer_num: int,
                                         datatype=0) -> Tuple[bool, bool]:
        """Determine if geometry should be filled in Ansys.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_num (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional):  Datatype of the layer number. Defaults to 0.

        Returns:
            Tuple[bool, bool]: 1st bool denotes if value for fill was available,
                            2nd value denotes value for fill. Default is None.
        """
        found_fill_value = False
        fill_value = None
        mask = (self.ls_df['layer']
                == layer_num) & (self.ls_df['datatype'] == datatype) & (
                    self.ls_df['chip_name'].str.contains(chip_name))
        search_result_df = self.ls_df[mask]
        if len(search_result_df) > 0:
            try:
                value = search_result_df.fill.iloc[0].strip('\'')
                if value in TRUE_STR:
                    found_fill_value = True
                    fill_value = True
                    return found_fill_value, fill_value
                if value in FALSE_STR:
                    found_fill_value = True
                    fill_value = False
                    return found_fill_value, fill_value
                self.logger.warning(
                    f'The \"fill\" value is neither True nor False.'
                    f'You have:{value}.  '
                    f'Will return NULL for fill value.')

            except Exception as ex:
                self._warning_search(chip_name, layer_num, datatype, ex)

        return found_fill_value, fill_value

    def get_z_coord_for_chip_and_layer(self,
                                       chip_name: str,
                                       layer_number: int,
                                       datatype: int = 0) -> float:
        """Using the layer_stack information, return the z_coord.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number. Defaults to 0.

        Returns:
           float: return the z_coord or 0.0 if not found in the dataframe.
        """
        z_coord = 0.0
        mask = (self.ls_df['layer']
                == layer_number) & (self.ls_df['datatype'] == datatype) & (
                    self.ls_df['chip_name'].str.contains(chip_name))
        search_result_df = self.ls_df[mask]
        if len(search_result_df) > 0:
            try:
                #Use the parse_values from Metal when parsing the values from layer_stack.

                z_coord = self.multi_planar_design.parse_value(
                    search_result_df.z_coord.iloc[0].strip('\''))
            except Exception as ex:
                self._warning_search(chip_name, layer_number, datatype, ex)

        return z_coord

    def get_thickness_for_chip_and_layer(self,
                                         chip_name: str,
                                         layer_number: int,
                                         datatype: int = 0) -> float:
        """Using the layer_stack information, return the thickness.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number. Defaults to 0.
        Returns:
           float: return the thickness or 0.0 if not found in the dataframe.
        """
        thickness = 0.0
        mask = (self.ls_df['layer']
                == layer_number) & (self.ls_df['datatype'] == datatype) & (
                    self.ls_df['chip_name'].str.contains(chip_name))
        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:
                thickness = parse_units(
                    search_result_df.thickness.iloc[0].strip('\''))
            except Exception as ex:
                self._warning_search(chip_name, layer_number, datatype, ex)

        return thickness

    def get_thickness_and_zcoord_for_chip_and_layer(
            self,
            chip_name: str,
            layer_number: int,
            datatype: int = 0) -> Tuple[float, float]:
        """Using the layer_stack information, return the thickness.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number. Defaults to 0.

        Returns:
           Tuple[float, float]:[ thickness, z_coord] return the thickness and z_coord
                            or 0.0 if not found in the dataframe.
        """
        thickness = 0.0
        z_coord = 0.0
        mask = (self.ls_df['layer']
                == layer_number) & (self.ls_df['datatype'] == datatype) & (
                    self.ls_df['chip_name'].str.contains(chip_name))
        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:

                thickness = self.multi_planar_design.parse_value(
                    search_result_df.thickness.iloc[0].strip('\''))
                z_coord = self.multi_planar_design.parse_value(
                    search_result_df.z_coord.iloc[0].strip('\''))
            except Exception as ex:
                self._warning_search(chip_name, layer_number, datatype, ex)

        return thickness, z_coord

    def get_zcoord_material_for_layer_datatype(self,
                                               layer_num: int,
                                               datatype: int = 0
                                              ) -> Tuple[float, str]:
        """ASSUME the layer_stack file has unique layer numbers.

        Args:
            layer_num (int): Unique layer number within layer stack.
            datatype (int, optional): Datatype of the layer number. Defaults to 0.

        Returns:
            Tuple[float,str]: The z_coord and material for given layer.
        """
        z_coord = 0.0
        material = None
        mask = (self.ls_df['layer'] == layer_num) & (self.ls_df['datatype']
                                                     == datatype)
        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:
                z_coord = self.multi_planar_design.parse_value(
                    search_result_df.z_coord.iloc[0].strip('\''))
                material = search_result_df.material.iloc[0].strip('\'')

            except Exception as ex:
                self._warning_search_layer_datatype(layer_num, datatype, ex)

        return z_coord, material

    def get_thickness_zcoord_material_for_layer_and_datatype(
            self,
            layer_number: int,
            datatype: int = 0) -> Tuple[float, float, str]:
        """Using the layer_stack information, return the thickness.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number. Defaults to 0.

        Returns:
           Tuple[float, float, str]:[ thickness, z_coord, material] return the
                            thickness, z_coord and material
                            or 0.0 for float and Null for str, if not found in the dataframe.
        """
        thickness = 0.0
        z_coord = 0.0
        material = None

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

            except Exception as ex:
                self._warning_search_layer_datatype(layer_number, datatype, ex)

        return thickness, z_coord, material

    def get_thickness_zcoord_material_for_chip_and_layer(
            self,
            chip_name: str,
            layer_number: int,
            datatype: int = 0) -> Tuple[float, float, str]:
        """Using the layer_stack information, return the thickness, z_coord, material.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number. Defaults to 0.

        Returns:
           Tuple[float, float, str]:[ thickness, z_coord, material] return the
                            thickness, z_coord and material
                            or 0.0 for float and Null for str, if not found in the dataframe.
        """
        thickness = 0.0
        z_coord = 0.0
        material = None

        mask = (self.ls_df['layer']
                == layer_number) & (self.ls_df['datatype'] == datatype) & (
                    self.ls_df['chip_name'].str.contains(chip_name))
        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:

                thickness = self.multi_planar_design.parse_value(
                    search_result_df.thickness.iloc[0].strip('\''))
                z_coord = self.multi_planar_design.parse_value(
                    search_result_df.z_coord.iloc[0].strip('\''))
                material = search_result_df.material.iloc[0].strip('\'')

            except Exception as ex:
                self._warning_search(chip_name, layer_number, datatype, ex)

        return thickness, z_coord, material

    def get_thickness_zcoord_material_fill_for_chip_and_layer(
            self,
            chip_name: str,
            layer_number: int,
            datatype: int = 0) -> Tuple[float, float, str, bool]:
        """Using the layer_stack information, return the thickness, z_coord, material and fill.

        Args:
            chip_name (str): Name of chip which has the layer of interest.
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            datatype (int, optional): Datatype of the layer number. Defaults to 0.

        Returns:
           Tuple[float, float, str, bool]:[ thickness, z_coord, material, fill] return the
                            thickness, z_coord, material, bool
                            or 0.0 for float and Null for str, if not found in the dataframe.
        """
        thickness = 0.0
        z_coord = 0.0
        material = None
        fill_value = None

        mask = (self.ls_df['layer']
                == layer_number) & (self.ls_df['datatype'] == datatype) & (
                    self.ls_df['chip_name'].str.contains(chip_name))
        search_result_df = self.ls_df[mask]

        if len(search_result_df) > 0:
            try:

                thickness = self.multi_planar_design.parse_value(
                    search_result_df.thickness.iloc[0].strip('\''))
                z_coord = self.multi_planar_design.parse_value(
                    search_result_df.z_coord.iloc[0].strip('\''))
                material = search_result_df.material.iloc[0].strip('\'')
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
            except Exception as ex:
                self._warning_search(chip_name, layer_number, datatype, ex)

        return thickness, z_coord, material, fill_value

    def get_unique_chip_names(self) -> set:
        """Get a set of unique names used in the layer_stack dataframe.

        Returns:
            set: Unique names used in the layer stack used as either default or provided by user.
        """
        names = self.ls_df['chip_name']
        result = set(names.str.strip('\''))
        return result

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

    def _warning_search_layer_datatype(self, layer_number: int, data_type: int,
                                       ex: Exception):
        """Give warning when the layerstack pandas table doesn't
        have requested layer information.

        Args:
            layer_number (int): The unique layer number through out all chips.
                            The same layer number can  not be used on multiple chips.
            data_type (int): _description_
            ex (Exception): _description_
        """

        self.logger.warning(
            f'\nERROR: {ex}'
            f'\nThere is an error searching in layer_stack dataframe using '
            f'layer={layer_number}, datatype={data_type}')
