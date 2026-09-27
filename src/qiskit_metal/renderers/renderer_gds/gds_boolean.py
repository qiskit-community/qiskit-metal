# This code is part of Quantum Metal.
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
"""Boolean operations for GDS export that stay correct on whole chips."""

import gdstk
import numpy as np

# Number of vertical strips a chip-sized boolean is split into.
GROUND_STRIPS = 16


def subtract_in_strips(
    base: list,
    cuts: list,
    layer: int,
    datatype: int,
    precision: float,
    strips: int = GROUND_STRIPS,
) -> list:
    """Return ``base`` minus ``cuts``, computed one vertical strip at a time.

    A single ``gdstk.boolean(base, cuts, "not")`` over a whole chip returns
    the ground as a polygon with every enclosed cut as a hole, and gdstk
    must link each hole to the outline. When it cannot, it prints
    "Unable to link hole in boolean operation" and drops the hole, so a
    whole line's gap comes out as solid ground. Slicing the base into
    strips first means a long cut network crosses strip edges instead of
    forming one large hole, and each strip only sees the cuts that
    overlap it. The output polygons meet along the strip edges.

    Args:
        base (list): Polygons to subtract from.
        cuts (list): Polygons or FlexPaths to subtract.
        layer (int): Layer of the result.
        datatype (int): Datatype of the result.
        precision (float): Boolean precision.
        strips (int): Number of vertical strips.

    Returns:
        list: The resulting ``gdstk.Polygon`` objects.
    """
    cut_polys = []
    for cut in cuts:
        cut_polys.extend(
            cut.to_polygons() if isinstance(cut, gdstk.FlexPath) else [cut]
        )
    base_polys = [
        poly
        for item in base
        for poly in (item.to_polygons() if isinstance(item, gdstk.FlexPath) else [item])
    ]
    if not base_polys:
        return []
    boxes = [poly.bounding_box() for poly in base_polys]
    x_min = min(b[0][0] for b in boxes)
    x_max = max(b[1][0] for b in boxes)
    if strips > 1 and x_max > x_min:
        edges = list(np.linspace(x_min, x_max, strips + 1)[1:-1])
        pieces = gdstk.slice(base_polys, edges, "x", precision)
    else:
        pieces = [base_polys]
    cut_spans = []
    for poly in cut_polys:
        box = poly.bounding_box()
        if box is not None:
            cut_spans.append((poly, box[0][0], box[1][0]))
    result = []
    for piece in pieces:
        if not piece:
            continue
        p_min = min(p.bounding_box()[0][0] for p in piece)
        p_max = max(p.bounding_box()[1][0] for p in piece)
        near = [c for c, c_min, c_max in cut_spans if c_max >= p_min and c_min <= p_max]
        result.extend(
            gdstk.boolean(
                piece,
                near,
                "not",
                layer=layer,
                datatype=datatype,
                precision=precision,
            )
        )
    return result
