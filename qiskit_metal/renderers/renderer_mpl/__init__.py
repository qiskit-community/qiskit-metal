# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
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


def plot_connectors(self, ax=None):
    '''
    Plots all connectors on the active axes. Draws the 1D line that
    represents the "port" of a connector point. These are referenced for smart placement
        of Metal components, such as when using functions like Metal_CPW_Connect.
    '''
    if ax is None:
        import matplotlib.pyplot as plt
        ax = plt.gca()

    for name, conn in self.connectors.items():
        line = LineString(conn.points)

        render_to_mpl(line, ax=ax, kw=dict(lw=2, c='r'))

        ax.annotate(name, xy=conn.middle[:2], xytext=conn.middle +
                    np.array(DEFAULT.annots.design_connectors_ofst),
                    **DEFAULT.annots.design_connectors)