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

from copy import deepcopy
from qiskit_metal.toolbox_python.attr_dict import Dict
from .base import QComponent


class BaseQubit(QComponent):
    """Qubit base class. Use to subscript, not to generate directly.

    Has connection lines that can be added

    Inherits components.QComponent class

    GUI interfaceing
        _img : set the name of the file such as 'Metal_Object.png'. YOu must place this
        file in the qiskit_metal._gui._imgs directory

    Default Options:
        * pos_x: '0um'
        * pos_y: '0um'
        * connection_pads: empty Dict -- The dictionary which contains all active connection lines for the qubit.
        * _default_connection_pads: empty Dict -- The default values for the (if any) connection lines of the qubit.
    """

    _img = 'Metal_Qubit.png'
    default_options = Dict(pos_x='0um',
                           pos_y='0um',
                           connection_pads=Dict(),
                           _default_connection_pads=Dict())
    """Default drawing options"""

    component_metadata = Dict(short_name='Q', _qgeometry_table_poly='True')
    """Component metadata"""

    TOOLTIP = """Qubit"""

    def __init__(self,
                 design,
                 name: str = None,
                 options: Dict = None,
                 options_connection_pads: dict = None,
                 make: bool = True):
        """
        Args:
            design (QDesign): The parent design.
            name (str): Name of the component.
            options (dict): User options that will override the defaults.  Defaults to None.
            component_template (dict): User can overwrite the template options for the component
                                       that will be stored in the design, in design.template,
                                       and used every time a new component is instantiated.
                                       Defaults to None.
            make (bool): True if the make function should be called at the end of the init.
                    Options be used in the make function to create the geometry.  Defaults to None.
        """
        super().__init__(design, name, options=options, make=False)

        if self.status == 'Not Built':
            # Component is not registered in design.
            # This qubit was not added to design.
            # self.logger.warning(
            # 'In BaseQubit.__init(), the qubit has not been added to design. The component is exiting with None.')
            return None
        if options_connection_pads:
            self.options.connection_pads.update(options_connection_pads)

        try:
            self._set_options_connection_pads()
        except Exception as e:
            raise Exception(
                f"Unable to create connection pads using given parameters: {options_connection_pads}.\n\n If given parameters is None, check to make sure you don't have any invalid child parameters in your connection_pads parameter.\n\n If you don't want any pads, ensure neither options_connection_pads nor options[connection_pads] are parameters\n\n Exception is: {e} "
            )
        if make:
            self.rebuild()

    def _set_options_connection_pads(self):
        """Applies the default options."""
        # class_name = type(self).__name__
        assert '_default_connection_pads' in self.design.template_options[
            self.class_name], f"""When
        you define your custom qubit class please add a _default_connection_pads
        dictionary name as default_options['_default_connection_pads']. This should specify the default
        creation options for the connection. """

        # Not sure if it best to remove it from options to keep
        del self.options._default_connection_pads
        # the self.options cleaner or not, since the options currently copies in the template. This is
        # potential source of bugs in the future
        for name in self.options.connection_pads:
            my_options_connection_pads = self.options.connection_pads[name]
            self.options.connection_pads[name] = deepcopy(
                self.design.template_options[
                    self.class_name]['_default_connection_pads'])
            self.options.connection_pads[name].update(
                my_options_connection_pads)
