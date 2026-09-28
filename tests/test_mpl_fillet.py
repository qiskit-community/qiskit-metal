"""The matplotlib renderer's corner fillet on straight and nearly straight corners.

On a straight run the unit vectors' dot product can round to just past -1;
``arccos`` then returned NaN, every check against NaN was False, and the
fillet points came out NaN -- drawn as a sawtooth of spikes along resampled
straight CPWs.
"""

import unittest

import numpy as np
from shapely.geometry import LineString, Point

from qiskit_metal.renderers.renderer_mpl.mpl_renderer import QMplRenderer


class _Renderer:
    fillet_path = QMplRenderer.fillet_path
    _calc_fillet = QMplRenderer._calc_fillet

    class design:  # noqa: N801 -- stands in for the design attribute
        class template_options:  # noqa: N801
            PRECISION = 9

    options = {"resolution": 16}


def _max_deviation(points, fillet=0.015):
    row = {"geometry": LineString(points), "fillet": fillet}
    drawn = _Renderer().fillet_path(row)
    coords = np.asarray(drawn.coords)
    if not np.all(np.isfinite(coords)):
        return np.inf
    return max(LineString(points).distance(Point(p)) for p in coords)


class TestNearlyStraightCorners(unittest.TestCase):
    def test_exactly_collinear(self):
        points = [(0, 0), (0.045, 0), (0.09, 0), (0.135, 0)]
        self.assertLess(_max_deviation(points), 1e-9)

    def test_dot_product_rounding_past_one(self):
        # A straight diagonal run from a real layout: the unit vectors' dot
        # product rounds to -1.0000000000000002 and arccos returned NaN.
        points = [
            (2.818971658, -4.900571658),
            (2.786907438, -4.868507438),
            (2.754843218, -4.836443218),
        ]
        self.assertLess(_max_deviation(points), 1e-9)

    def test_real_corner_is_still_filleted(self):
        points = [(0, 0), (0.1, 0), (0.1, 0.1)]
        row = {"geometry": LineString(points), "fillet": 0.02}
        drawn = _Renderer().fillet_path(row)
        self.assertGreater(len(drawn.coords), len(points))
        self.assertLess(_max_deviation(points, fillet=0.02), 0.02)


if __name__ == "__main__":
    unittest.main()
