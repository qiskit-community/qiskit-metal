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
"""File contains basic dictionaries.

File contains a class to contain the basic dictionaries.
"""

from copy import deepcopy

from qiskit_metal.toolbox_python.attr_dict import Dict


class DefaultMetalOptions(Dict):
    """`DefaultMetalOptions` is the container for the default options used in:

        1. Components - each time a new component is registered (instantiated).
        2. The metal code codebase, in functions such as drawing and in qdesign base

    Args:
        generic (Dict): Dictionary of options.  Defaults to None.
    """

    default_generic = Dict(
        units='mm',  # Units in which all dimensions are converted as floats
        chip=
        'main',  # Default chip used through codebase, when one is not specified

        # Default options for QDesign variables
        qdesign=Dict(variables=Dict(cpw_width='10 um', cpw_gap='6 um')),

        # Used for numpy.round()
        PRECISION=9,

        # Geometric
        geometry=Dict(
            buffer_resolution=16,  # for shapely buffer
            buffer_mitre_limit=5.0,
        ))
    """
    Define the default generic properties
    """

    def __init__(self, generic: Dict = None):
        """The constructor for the `DefaultMetalOptions` class."""
        if not generic:
            generic = deepcopy(self.default_generic)

        # self._generic = deepcopy(generic) # Do we need to save this?
        super().__init__()
        self.update(generic)

    def update_default_options(self, cust_key: str, cust_value=None):
        """Allow instance of class to update the default_options.

        Args:
            cust_key (str): Type of component
            cust_value (object): Value for the given key.  Defaults to None.
        """
        self[cust_key] = cust_value


# Can't really use this until default_draw_substrate.color_plane is resolved.
class DefaultOptionsRenderer():  # pylint: disable=too-few-public-methods
    """`DefaultOptionsRenderer` is the class that encapsulate generic data used
    throughout qiskit metal classes for renderers.

    This class is a skeleton and is expected to be updated when the renderer is updated.

    Args:
        draw_substrate (Dict): This is the dictionary defining the draw substrate parameters.
        bounding_box (Dict): This is the dictionary defining the bounding box parameters.
    """

    # These are potential dicts that could be used for renderers.
    default_bounding_box = Dict(
        draw_bounding_box=[[0, 0], [0, 0], ['0.890mm', '0.900mm']])
    """
    Define the default bounding box.
    """

    default_draw_substrate = Dict(
        draw_substrate={
            'pos_xy': "['0um', '0um']",
            'size': "['8.5mm', '6.5mm', '-0.750mm']",
            'elevation': 0,
            'ground_plane': 'ground_plane',
            'substrate': 'substrate',
            'material': 'silicon',
            # 'color_plane': DEFAULT.colors.ground_main,      #this needs to change
            'transparency_plane': 0,
            'transparency_substrate': 0,
            'wireframe_substrate': False
        })
    """
    Define the default draw substrate
    """

    def __init__(self,
                 draw_substrate: Dict = default_draw_substrate,
                 bounding_box: Dict = default_bounding_box):
        """The constructor for the `DefaultOptionsRenderer` class."""
        #self.logger = logger

        # Do Not edit the class variable
        self.draw_substrate = deepcopy(draw_substrate)
        self.bounding_box = deepcopy(bounding_box)

        # custom default options
        self.default_options = {}
        self.default_options.update(self.draw_substrate)
        self.default_options.update(self.bounding_box)

    # customize the key/value pairs
    def update_default_options(self,
                               cust_key: str = None,
                               cust_value: Dict = None):
        """Allow instance of class to update the default_options.

        Args:
            cust_key (str): Type of component.  Defaults to None.
            cust_value (Dict): The key/value pairs to describe component.  Defaults to None.

        Returns:
            The return value. True for success, False otherwise.
        """
        assert (cust_key is not None
               ), f'ERROR: Need a key, update_default_options has {cust_key}'
        self.default_options[cust_key] = cust_value
