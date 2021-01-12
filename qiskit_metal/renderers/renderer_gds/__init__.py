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
@auhtor: Zlatko Minev
@date: 2019
"""


def gds_draw_all(self, path=None):
    r'''
    Create full gds export cell

    path : str : if passed will save

    Can see with
        gdspy.LayoutViewer()

    can save with
        # Save all created cells in file 'first.gds'
        path = r'C:\zkm\2019-hfss\gds'
        gdspy.write_gds(path+r'\first.gds')
    '''
    import gdspy

    gdspy.current_library.cell_dict.clear()
    device = gdspy.Cell('TOP_CELL')
    for _, obj in self.qlibrary.items():
        if is_component(obj):
            cell = obj.gds_draw()
            device.add(gdspy.CellReference(cell))

    if path:
        gdspy.write_gds(path)

    return gdspy.current_library.cell_dict
