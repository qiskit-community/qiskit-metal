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

import contextlib
import os
import sys

import gdstk
import numpy as np
import shapely
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

# Number of vertical strips a chip-sized boolean is split into.
GROUND_STRIPS = 16


def remove_cell(lib: gdstk.Library, cell: gdstk.Cell) -> None:
    """Remove ``cell`` from ``lib`` together with every reference to it.

    ``gdstk.Library.remove`` removes only the cell; references to it stay
    in their parent cells and are written to the file as references to a
    missing cell (gdspy's ``remove(..., remove_references=True)`` did both).
    """
    for parent in lib.cells:
        stale = [ref for ref in parent.references if ref.cell is cell]
        if stale:
            parent.remove(*stale)
    lib.remove(cell)


def subtract_in_strips(
    base: list,
    cuts: list,
    layer: int,
    datatype: int,
    precision: float,
    strips: int = GROUND_STRIPS,
) -> list:
    """Return ``base`` minus ``cuts``, computed one vertical strip at a time.

    ``gdstk.boolean(base, cuts, "not")`` returns the ground with every
    enclosed cut as a hole, and must link each hole to its outline. When it
    cannot, it prints "Unable to link hole in boolean operation" and drops
    the hole or writes a self-intersecting polygon -- a whole line's gap can
    come out as solid ground. Two defenses:

    * The base is sliced into strips, and each strip is subtracted against
      only the cuts that overlap it, so a long cut network crosses strip
      edges instead of forming one large hole. This is also much faster.
    * Each strip's result is checked against the same difference computed
      with shapely (GEOS), which keeps holes as holes. If gdstk's area
      differs, the strip is rebuilt from
      the shapely result, split into polygons without holes.

    The output polygons meet along the strip edges.

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
    cut_polys = _as_polygons(cuts)
    base_polys = _as_polygons(base)
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
        span = poly.bounding_box()
        if span is not None:
            cut_spans.append((poly, span[0][0], span[1][0]))
    result = []
    for piece in pieces:
        if not piece:
            continue
        p_min = min(p.bounding_box()[0][0] for p in piece)
        p_max = max(p.bounding_box()[1][0] for p in piece)
        near = [c for c, c_min, c_max in cut_spans if c_max >= p_min and c_min <= p_max]
        with _quiet_c_stderr():
            fast = gdstk.boolean(
                piece, near, "not", layer=layer, datatype=datatype, precision=precision
            )
        exact = _shapely(piece).difference(_shapely(near)) if near else _shapely(piece)
        if _agrees(fast, exact, precision):
            result.extend(fast)
        else:
            result.extend(_without_holes(exact, layer, datatype))
    return result


@contextlib.contextmanager
def _quiet_c_stderr():
    """Silence gdstk's C-level stderr for one call.

    gdstk reports a hole it cannot link on stderr, from C. The result is
    checked and rebuilt when wrong, so the message would only mislead. C code
    writes to file descriptor 2 whatever ``sys.stderr`` is (in Jupyter it is
    not a file), so that is the descriptor redirected.
    """
    fd = 2
    try:
        saved = os.dup(fd)
    except OSError:
        yield
        return
    try:
        for stream in (sys.stderr, sys.__stderr__):
            with contextlib.suppress(Exception):
                stream.flush()
        with open(os.devnull, "w") as devnull:
            os.dup2(devnull.fileno(), fd)
            try:
                yield
            finally:
                os.dup2(saved, fd)
    finally:
        os.close(saved)


def _as_polygons(items: list) -> list:
    """Flatten a mix of ``gdstk.Polygon`` and ``gdstk.FlexPath`` to polygons."""
    polys = []
    for item in items:
        polys.extend(item.to_polygons() if isinstance(item, gdstk.FlexPath) else [item])
    return polys


def _shapely(polys: list):
    """Union of gdstk polygons as one shapely geometry.

    gdstk fills with the nonzero rule, so where a path overlaps itself the
    doubly covered area is inside. The default ``make_valid`` treats that as
    a hole; the "structure" method (shapely 2.1+) and ``buffer(0)`` do not.
    """
    shapes = [Polygon(p.points) for p in polys if len(p.points) >= 3]
    return unary_union([_nonzero_valid(s) for s in shapes])


def _nonzero_valid(poly):
    """``poly`` made valid, keeping self-overlapping regions filled."""
    if poly.is_valid:
        return poly
    try:
        return shapely.make_valid(poly, method="structure")
    except TypeError:  # shapely < 2.1
        return poly.buffer(0)


def _agrees(fast: list, exact, precision: float) -> bool:
    """True if gdstk's polygons cover the same area as ``exact``.

    A dropped or mislinked hole changes the area by the hole's area. gdstk
    joins each hole to its outline with a zero-width seam, so its output is
    not "valid" to shapely even when it is correct; the area is the test.
    """
    covered = sum(Polygon(p.points).area for p in fast if len(p.points) >= 3)
    # Allow the rounding of every vertex to ``precision`` along the outline.
    tolerance = max(exact.length, 1.0) * precision * 10
    return abs(covered - exact.area) <= tolerance


def _without_holes(geometry, layer: int, datatype: int) -> list:
    """``gdstk.Polygon`` objects covering ``geometry``, none with a hole.

    A polygon with holes is split along a vertical line through the middle of
    one hole's bounding box -- a line that always crosses a connected hole --
    until no piece has a hole left.
    """
    out = []
    stack = _parts(geometry)
    while stack:
        poly = stack.pop()
        if poly.is_empty or poly.area == 0:
            continue
        if not poly.interiors:
            out.append(
                gdstk.Polygon(
                    list(poly.exterior.coords)[:-1], layer=layer, datatype=datatype
                )
            )
            continue
        h_min, _, h_max, _ = poly.interiors[0].bounds
        x = (h_min + h_max) / 2
        minx, miny, maxx, maxy = poly.bounds
        for half in (box(minx, miny, x, maxy), box(x, miny, maxx, maxy)):
            stack.extend(_parts(poly.intersection(half)))
    return out


def _parts(geometry) -> list:
    """The polygons in a shapely geometry (dropping lines and points)."""
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    if hasattr(geometry, "geoms"):
        return [p for g in geometry.geoms for p in _parts(g)]
    return []
