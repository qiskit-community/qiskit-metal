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
"""Module containing the basic planar (2D) design for CPW-style geometries."""

from typing import Tuple, Optional
from qiskit_metal.designs.design_base import QDesign, Dict

__all__ = ['DesignPlanar']


class DesignPlanar(QDesign):
    """Planar (2D) design with a single chip and CPW-style geometries.

    Use this as the default design class when you are laying out coplanar
    waveguides, qubits, resonators, and other planar components on a single
    dielectric/metal stack.

    What this design manages for you:

    - Chip metadata: material, layer span, and a default chip size and origin.
      The defaults are centered at ``(0, 0)`` with a 9 mm x 6 mm footprint and
      a finite thickness in ``z``. Adjust these in ``self._chips`` or through
      your YAML/options before exporting.
    - Coordinate system: everything is centered at the chip origin; renders and
      exports use these bounds for clipping, subtraction, and cheesing.
    - Renderer enablement: set ``enable_renderers=False`` if you want a pure
      geometry run without renderer bootstrapping.

    Typical workflow:

    #. Instantiate ``DesignPlanar`` with optional metadata and renderer control.
    #. Add QComponents (qubits, resonators, launch pads, routes) to the design.
    #. Use the chip size helpers (e.g., ``get_x_y_for_chip``) to clip or subtract
       geometries during export.
    #. Run your renderer of choice (GDS, Ansys, etc.) using the design’s tables.

    Philosophy and extensions:

    - Keep it simple and fast: this design is intentionally minimal—one chip,
      one stack—so iteration is quick. Start here unless you explicitly need
      multiple substrates or flip-chip structures.
    - Need multiple chips or 3D stacking? Switch to ``MultiPlanar`` or
      ``DesignFlipChip``; the API is similar, but those classes manage multiple
      chip entries and inter-chip alignments.
    - Chip size and origin matter: routing, subtraction, and cheesing rely on
      the chip bounds. Adjust ``self._chips['main']['size']`` early to avoid
      surprises in exports.
    """

    def __init__(self,
                 metadata: Optional[dict] = None,
                 overwrite_enabled: bool = False,
                 enable_renderers: bool = True):
        """Create a planar design with optional metadata and renderer control.

        Args:
            metadata: Optional metadata dict to annotate the design (e.g.,
                owner, project, notes). Passed through to ``QDesign``.
            overwrite_enabled: Allow overwriting existing component names.
                Keep False to catch accidental collisions.
            enable_renderers: Initialize renderer registration on creation.
                Set False for lightweight geometry-only workflows.
        """

        super().__init__(metadata=metadata,
                         overwrite_enabled=overwrite_enabled,
                         enable_renderers=enable_renderers)
        self.add_chip_info()

    def add_chip_info(self):
        """TODO How to get the values into self.chip. Will need to set up
        parser for "self.p" for design base. For now, just hard code in
        something.

        # GDSTK is using numbers based on 1 meter unit.
        # When the gds file is exported, data is converted to "user-selected" units.
        # centered at (0,0) and 9 by 6 size.

        NOTE: self._chips dict comes from QDesign base class.
        """
        self._chips['main'] = Dict(
            material='silicon',
            layer_start='0',
            layer_end='2048',
        )

        self._chips['main']['size'] = Dict(
            center_x='0.0mm',
            center_y='0.0mm',
            center_z='0.0mm',
            size_x='9mm',
            size_y='6mm',
            size_z='-750um',  # chip extends in negative z direction by 750 um
            sample_holder_top='890um',  # how tall is the vacuum above center_z
            sample_holder_bottom='1650um'  # how tall is the vacuum below z=0
        )

    def get_x_y_for_chip(
            self,
            chip_name: str) -> Tuple[Tuple[float, float, float, float], int]:
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
