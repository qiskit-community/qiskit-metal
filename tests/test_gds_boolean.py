"""subtract_in_strips: the chip-sized boolean used for ground and cheesing.

A single gdstk "not" over a whole chip can fail to link a hole ("Unable to
link hole in boolean operation") and silently drop it; on a 17-qubit chip
three whole flux-line gaps came out as solid ground. The helper slices the
base into strips first. These tests check that the result is the same
region the plain boolean should give.
"""

import unittest
from unittest import mock

import gdstk
from shapely.geometry import box as shapely_box

from qiskit_metal.renderers.renderer_gds import gds_boolean
from qiskit_metal.renderers.renderer_gds.gds_boolean import subtract_in_strips

PRECISION = 1e-9


def _area(polys):
    return sum(p.area() for p in polys)


def _chip(size=10.0):
    h = size / 2
    return gdstk.rectangle((-h, -h), (h, h), layer=1)


class TestSubtractInStrips(unittest.TestCase):
    def test_long_cut_across_many_strips(self):
        # A long, bent "line gap" crossing most of the chip.
        cut = gdstk.FlexPath([(-4.5, -4), (4, -4), (4, 4), (-4, 4)], 0.02)
        out = subtract_in_strips(
            [_chip()], [cut], layer=1, datatype=0, precision=PRECISION
        )
        expected = _chip().area() - _area(cut.to_polygons())
        self.assertAlmostEqual(_area(out), expected, places=6)

    def test_enclosed_cut_network(self):
        # A closed ring of cut encloses a ground island; a line inside it.
        ring = gdstk.FlexPath([(-3, -3), (3, -3), (3, 3), (-3, 3), (-3, -3)], 0.02)
        inner = gdstk.FlexPath([(-2, 0), (2, 0)], 0.02)
        out = subtract_in_strips(
            [_chip()], [ring, inner], layer=1, datatype=0, precision=PRECISION
        )
        cut_area = _area(gdstk.boolean(ring.to_polygons(), inner.to_polygons(), "or"))
        self.assertAlmostEqual(_area(out), _chip().area() - cut_area, places=6)

    def test_strip_count_does_not_change_the_region(self):
        cuts = [
            gdstk.rectangle((x, -4), (x + 0.1, 4))
            for x in (-3.95, -1.0, 0.3, 2.2)  # some straddle strip edges
        ]
        one = subtract_in_strips(
            [_chip()], cuts, layer=1, datatype=0, precision=PRECISION, strips=1
        )
        many = subtract_in_strips(
            [_chip()], cuts, layer=1, datatype=0, precision=PRECISION, strips=16
        )
        self.assertAlmostEqual(_area(one), _area(many), places=6)
        self.assertAlmostEqual(_area(many), _chip().area() - 4 * 0.1 * 8, places=6)

    def test_layer_and_datatype(self):
        out = subtract_in_strips(
            [_chip()],
            [gdstk.rectangle((0, 0), (1, 1))],
            layer=3,
            datatype=7,
            precision=PRECISION,
        )
        self.assertTrue(out)
        self.assertTrue(all(p.layer == 3 and p.datatype == 7 for p in out))

    def test_empty_base(self):
        self.assertEqual(
            subtract_in_strips([], [], layer=1, datatype=0, precision=PRECISION), []
        )


class TestFallback(unittest.TestCase):
    """When gdstk's result is wrong, the strip is rebuilt from shapely."""

    def test_dropped_result_is_repaired(self):
        cuts = [gdstk.rectangle((-1, -1), (1, 1)), gdstk.rectangle((2, 2), (3, 4))]
        expected = _chip().area() - 4 - 2
        real_boolean = gdstk.boolean

        def lossy(*args, **kwargs):  # a gdstk that silently drops every hole
            return real_boolean(args[0], [], "not", **kwargs)

        with mock.patch.object(gds_boolean.gdstk, "boolean", side_effect=lossy):
            out = subtract_in_strips(
                [_chip()], cuts, layer=1, datatype=0, precision=PRECISION, strips=1
            )
        self.assertAlmostEqual(_area(out), expected, places=6)

    def test_without_holes_keeps_area_and_removes_holes(self):
        square = shapely_box(-5, -5, 5, 5)
        holes = square.difference(shapely_box(-1, -1, 1, 1)).difference(
            shapely_box(2, 2, 3, 4)
        )
        out = gds_boolean._without_holes(holes, layer=1, datatype=0)
        self.assertAlmostEqual(_area(out), holes.area, places=9)
        for poly in out:  # a gdstk polygon has no holes; check it is simple
            self.assertGreater(poly.area(), 0)


if __name__ == "__main__":
    unittest.main()
