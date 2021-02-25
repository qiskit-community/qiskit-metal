# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
@author: Marco Facchini (IBM)
@date: 2020
"""

from . import QRenderer
from ... import Dict
from abc import abstractmethod, ABC

from ...designs import QDesign, is_design


__all__ = ['QRendererAnalysis']


class QRendererAnalysis(QRenderer):
    """Abstract base class for all Renderers intended for Analysis.
    """
    def __init__(self,
                 design: 'QDesign',
                 initiate=False,
                 options: Dict = None):
        """
        Args:
            design (QDesign): The design
            initiate (bool): True to initiate the renderer (Default: False)
            settings (Dict, optional): Used to override default settings. Defaults to None.
        """
        super().__init__(design=design,
                         initiate=initiate,
                         render_options=options)

    @abstractmethod
    def initialized(self):
        """
        Renderer ready to be used?
        
        Implementation must return boolean True if succesful. False otherwise.
        """
        return True


# class Cap():
#     def
