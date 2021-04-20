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

# pylint: disable-msg=unnecessary-pass
# pylint: disable-msg=too-many-public-methods
# pylint: disable-msg=broad-except
# pylint: disable-msg=import-error
"""Qiskit Metal unit tests components functionality."""

import unittest
import numpy as np

from qiskit_metal.qlibrary.core import QComponent
from qiskit_metal.qlibrary.core import QRoute
from qiskit_metal.qlibrary.core import QRouteLead
from qiskit_metal.qlibrary.core import QRoutePoint
from qiskit_metal.qlibrary.core import BaseQubit
from qiskit_metal.qlibrary.sample_shapes.circle_caterpillar import CircleCaterpillar
from qiskit_metal.qlibrary.sample_shapes.circle_raster import CircleRaster
from qiskit_metal.qlibrary.sample_shapes.rectangle import Rectangle
from qiskit_metal.qlibrary.sample_shapes.rectangle_hollow import RectangleHollow
from qiskit_metal.qlibrary.sample_shapes.n_gon import NGon
from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
from qiskit_metal.qlibrary.lumped.cap_n_interdigital import CPWFingerCap
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CPWHangerT
from qiskit_metal.qlibrary.couplers.cap_n_interdigital_tee import CPWTFingerCap
from qiskit_metal.qlibrary.couplers.tee import CPWT
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround
from qiskit_metal.qlibrary.tlines.anchored_path import RouteAnchors
from qiskit_metal.qlibrary.tlines.framed_path import RouteFramed
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.qlibrary.tlines.mixed_path import RouteMixed
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.launchpad_wb_coupled import LaunchpadWirebondCoupled
from qiskit_metal.qlibrary.lumped.cap_3_interdigital import CapThreeFingers
from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_cross_fl import TransmonCrossFL
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_pocket_cl import TransmonPocketCL
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.couplers.tunable_coupler_01 import TunableCoupler01
from qiskit_metal import designs
from qiskit_metal.qlibrary._template import MyQComponent
from qiskit_metal.tests.assertions import AssertionsMixin

#pylint: disable-msg=line-too-long
from qiskit_metal.qlibrary.lumped.resonator_coil_rect import ResonatorRectangleSpiral


class TestComponentInstantiation(unittest.TestCase, AssertionsMixin):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_qlibrary_instantiate_qcomponent(self):
        """Test the instantiaion of QComponent."""
        design = designs.DesignPlanar()
        try:
            QComponent
        except Exception:
            self.fail("QComponent failed")

        with self.assertRaises(NotImplementedError):
            QComponent(design, "my_name")

        with self.assertRaises(NotImplementedError):
            QComponent(design, "my_name2", options={})

        try:
            QComponent(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "QComponent(design, \"my_name3\", options={}, make=False)")

        try:
            QComponent(design,
                       "my_name4",
                       options={},
                       make=False,
                       component_template={})
        except Exception:
            msg = "QComponent(design, \"my_name4\", options={}, make=False, component_template={})"
            self.fail(msg)

    def test_qlibrary_instantiate_basequbit(self):
        """Test the instantiation of basequbit."""
        design = designs.DesignPlanar()
        try:
            BaseQubit
        except Exception:
            self.fail("BaseQubit failed")

        with self.assertRaises(NotImplementedError):
            BaseQubit(design, "my_name")

        with self.assertRaises(NotImplementedError):
            BaseQubit(design, "my_name2", options={})

        try:
            BaseQubit(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail("BaseQubit(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_open_to_ground(self):
        """Test the instantiation of openToGround."""
        design = designs.DesignPlanar()
        try:
            OpenToGround
        except Exception:
            self.fail("OpenToGround failed")

        try:
            OpenToGround(design, "my_name")
        except Exception:
            self.fail("OpenToGround(design, \"my_name\")")

        try:
            OpenToGround(design, "my_name2", options={})
        except Exception:
            self.fail("OpenToGround(design, \"my_name2\", options={})")

        try:
            OpenToGround(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "OpenToGround(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_short_to_ground(self):
        """Test the instantiation of shortToGround."""
        design = designs.DesignPlanar()
        try:
            ShortToGround
        except Exception:
            self.fail("ShortToGround failed")

        try:
            ShortToGround(design, "my_name")
        except Exception:
            self.fail("ShortToGround(design, \"my_name\")")

        try:
            ShortToGround(design, "my_name2", options={})
        except Exception:
            self.fail("ShortToGround(design, \"my_name2\", options={})")

        try:
            ShortToGround(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "ShortToGround(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_route_frame_path(self):
        """Test the instantiation of RouteFramed."""
        try:
            RouteFramed
        except Exception:
            self.fail("RouteFramed failed")

    def test_qlibrary_instantiate_route_straight(self):
        """Test the instantiation of RouteStraight."""
        design = designs.DesignPlanar()
        try:
            RouteStraight
        except Exception:
            self.fail("RouteStraight failed")

        try:
            RouteStraight(design, "my_name2", options={})
        except Exception:
            self.fail("RouteStraight(design, \"my_name2\", options={})")

        try:
            RouteStraight(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "RouteStraight(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_q_route_lead(self):
        """Test the instantiation of QRouteLead."""
        try:
            QRouteLead
        except Exception:
            self.fail("QRouteLead failed")

    def test_qlibrary_instantiate_q_route_point(self):
        """Test the instantiation of QRoutePoint."""
        try:
            QRoutePoint(np.array([1, 2]))
        except Exception:
            self.fail("QRoutePoint failed")

    def test_qlibrary_instantiate_route_meander(self):
        """Test the instantiation of RouteMeander."""
        try:
            RouteMeander
        except Exception:
            self.fail("RouteMeander failed")

    def test_qlibrary_instantiate_route_mixed(self):
        """Test the instantiation of RouteMixed."""
        try:
            RouteMixed
        except Exception:
            self.fail("RouteMixed failed")

    def test_qlibrary_instantiate_q_route(self):
        """Test the instantiation of QRoute."""
        design = designs.DesignPlanar()
        try:
            QRoute(design, name='test_qroute', options={})
        except Exception:
            self.fail("QRoute failed")

    def test_qlibrary_instantiate_my_q_component(self):
        """Test the instantiation of MyQComponent."""
        design = designs.DesignPlanar()
        try:
            MyQComponent
        except Exception:
            self.fail("MyQComponent failed")

        try:
            MyQComponent(design, "my_name")
        except Exception:
            self.fail("MyQComponent(design, \"my_name\")")

        try:
            MyQComponent(design, "my_name2", options={})
        except Exception:
            self.fail("MyQComponent(design, \"my_name2\", options={})")

        try:
            MyQComponent(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "MyQComponent(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_cpw_finger_cap(self):
        """Test the instantiation of CPWFingerCap."""
        design = designs.DesignPlanar()
        try:
            CPWFingerCap
        except Exception:
            self.fail("CPWFingerCap failed")

        try:
            CPWFingerCap(design, "my_name")
        except Exception:
            self.fail("CPWFingerCap(design, \"my_name\")")

        try:
            CPWFingerCap(design, "my_name2", options={})
        except Exception:
            self.fail("CPWFingerCap(design, \"my_name2\", options={})")

        try:
            CPWFingerCap(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "CPWFingerCap(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_cpw_t_finger_cap(self):
        """Test the instantiation of CPWTFingerCap."""
        design = designs.DesignPlanar()
        try:
            CPWTFingerCap
        except Exception:
            self.fail("CPWTFingerCap failed")

        try:
            CPWTFingerCap(design, "my_name")
        except Exception:
            self.fail("CPWTFingerCap(design, \"my_name\")")

        try:
            CPWTFingerCap(design, "my_name2", options={})
        except Exception:
            self.fail("CPWTFingerCap(design, \"my_name2\", options={})")

        try:
            CPWTFingerCap(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "CPWTFingerCap(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_cpw_t(self):
        """Test the instantiation of CPWT."""
        design = designs.DesignPlanar()
        try:
            CPWT
        except Exception:
            self.fail("CPWT failed")

        try:
            CPWT(design, "my_name")
        except Exception:
            self.fail("CPWT(design, \"my_name\")")

        try:
            CPWT(design, "my_name2", options={})
        except Exception:
            self.fail("CPWT(design, \"my_name2\", options={})")

        try:
            CPWT(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail("CPWT(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_cpw_hanger_t(self):
        """Test the instantiation of CPWHangerT."""
        design = designs.DesignPlanar()
        try:
            CPWHangerT
        except Exception:
            self.fail("CPWHangerT failed")

        try:
            CPWHangerT(design, "my_name")
        except Exception:
            self.fail("CPWHangerT(design, \"my_name\")")

        try:
            CPWHangerT(design, "my_name2", options={})
        except Exception:
            self.fail("CPWHangerT(design, \"my_name2\", options={})")

        try:
            CPWHangerT(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "CPWHangerT(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_resonator_rectangle_spiral(self):
        """Test the instantiation of ResonatorRectangleSpiral."""
        design = designs.DesignPlanar()
        try:
            ResonatorRectangleSpiral
        except Exception:
            self.fail("ResonatorRectangleSpiral failed")

        try:
            ResonatorRectangleSpiral(design, "my_name")
        except Exception:
            self.fail("ResonatorRectangleSpiral(design, \"my_name\")")

        try:
            ResonatorRectangleSpiral(design, "my_name2", options={})
        except Exception:
            self.fail(
                "ResonatorRectangleSpiral(design, \"my_name2\", options={})")

        try:
            ResonatorRectangleSpiral(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "ResonatorRectangleSpiral(design, \"my_name3\", options={}, make=False)"
            )

    def test_qlibrary_instantiate_circle_raster(self):
        """Test the instantiation of CircleRaster."""
        design = designs.DesignPlanar()
        try:
            CircleRaster
        except Exception:
            self.fail("CircleRaster failed")

        try:
            CircleRaster(design, "my_name")
        except Exception:
            self.fail("CircleRaster(design, \"my_name\")")

        try:
            CircleRaster(design, "my_name2", options={})
        except Exception:
            self.fail("CircleRaster(design, \"my_name2\", options={})")

        try:
            CircleRaster(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "CircleRaster(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_circle_caterpillar(self):
        """Test the instantiation of CircleCaterpillar."""
        design = designs.DesignPlanar()
        try:
            CircleCaterpillar
        except Exception:
            self.fail("CircleCaterpillar failed")

        try:
            CircleCaterpillar(design, "my_name")
        except Exception:
            self.fail("CircleCaterpillar(design, \"my_name\")")

        try:
            CircleCaterpillar(design, "my_name2", options={})
        except Exception:
            self.fail("CircleCaterpillar(design, \"my_name2\", options={})")

        try:
            CircleCaterpillar(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "CircleCaterpillar(design, \"my_name3\", options={}, make=False)"
            )

    def test_qlibrary_instantiate_n_gon(self):
        """Test the instantiation of NGon."""
        design = designs.DesignPlanar()
        try:
            NGon
        except Exception:
            self.fail("NGon failed")

        try:
            NGon(design, "my_name")
        except Exception:
            self.fail("NGon(design, \"my_name\")")

        try:
            NGon(design, "my_name2", options={})
        except Exception:
            self.fail("NGon(design, \"my_name2\", options={})")

        try:
            NGon(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail("NGon(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_n_square_spiral(self):
        """Test the instantiation of NSquareSpiral."""
        design = designs.DesignPlanar()
        try:
            NSquareSpiral
        except Exception:
            self.fail("NSquareSpiral failed")

        try:
            NSquareSpiral(design, "my_name")
        except Exception:
            self.fail("NSquareSpiral(design, \"my_name\")")

        try:
            NSquareSpiral(design, "my_name2", options={})
        except Exception:
            self.fail("NSquareSpiral(design, \"my_name2\", options={})")

        try:
            NSquareSpiral(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "NSquareSpiral(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_rectangle(self):
        """Test the instantiation of Rectangle."""
        design = designs.DesignPlanar()
        try:
            Rectangle
        except Exception:
            self.fail("Rectangle failed")

        try:
            Rectangle(design, "my_name")
        except Exception:
            self.fail("Rectangle(design, \"my_name\")")

        try:
            Rectangle(design, "my_name2", options={})
        except Exception:
            self.fail("Rectangle(design, \"my_name2\", options={})")

        try:
            Rectangle(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail("Rectangle(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_rectangle_hollow(self):
        """Test the instantiation of RectangleHollow."""
        design = designs.DesignPlanar()
        try:
            RectangleHollow
        except Exception:
            self.fail("RectangleHollow failed")

        try:
            RectangleHollow(design, "my_name")
        except Exception:
            self.fail("RectangleHollow(design, \"my_name\")")

        try:
            RectangleHollow(design, "my_name2", options={})
        except Exception:
            self.fail("RectangleHollow(design, \"my_name2\", options={})")

        try:
            RectangleHollow(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "RectangleHollow(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_route_anchors(self):
        """Test the instantiation of RouteAnchors."""
        design = designs.DesignPlanar()
        try:
            RouteAnchors
        except Exception:
            self.fail("RouteAnchors failed")

        try:
            RouteAnchors(design, "my_name2", options={})
        except Exception:
            self.fail("RouteAnchors(design, \"my_name2\", options={})")

        try:
            RouteAnchors(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "RouteAnchors(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_route_pathfinder(self):
        """Test the instantiation of RoutePathfinder."""
        design = designs.DesignPlanar()
        try:
            RoutePathfinder
        except Exception:
            self.fail("RoutePathfinder failed")

        try:
            RoutePathfinder(design, "my_name2", options={})
        except Exception:
            self.fail("RoutePathfinder(design, \"my_name2\", options={})")

        try:
            RoutePathfinder(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "RoutePathfinder(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_instantiate_launch_v1(self):
        """Test the instantiation of LaunchpadWirebond."""
        design = designs.DesignPlanar()
        try:
            LaunchpadWirebond
        except Exception:
            self.fail("LaunchpadWirebond failed")

        try:
            LaunchpadWirebond(design, "my_name")
        except Exception:
            self.fail("LaunchpadWirebond(design, \"my_name\")")

        try:
            LaunchpadWirebond(design, "my_name2", options={})
        except Exception:
            self.fail("LaunchpadWirebond(design, \"my_name2\", options={})")

        try:
            LaunchpadWirebond(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "LaunchpadWirebond(design, \"my_name3\", options={}, make=False)"
            )

    def test_qlibrary_instantiate_launch_v2(self):
        """Test the instantiation of LaunchpadWirebondCoupled."""
        design = designs.DesignPlanar()
        try:
            LaunchpadWirebondCoupled
        except Exception:
            self.fail("LaunchpadWirebondCoupled failed")

        try:
            LaunchpadWirebondCoupled(design, "my_name")
        except Exception:
            self.fail("LaunchpadWirebondCoupled(design, \"my_name\")")

        try:
            LaunchpadWirebondCoupled(design, "my_name2", options={})
        except Exception:
            self.fail(
                "LaunchpadWirebondCoupled(design, \"my_name2\", options={})")

        try:
            LaunchpadWirebondCoupled(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "LaunchpadWirebondCoupled(design, \"my_name3\", options={}, make=False)"
            )

    def test_qlibrary_instantiate_three_finger_cap_v1(self):
        """Test the instantiation of CapThreeFingers."""
        design = designs.DesignPlanar()
        try:
            CapThreeFingers
        except Exception:
            self.fail("CapThreeFingers failed")

        try:
            CapThreeFingers(design, "my_name")
        except Exception:
            self.fail("CapThreeFingers(design, \"my_name\")")

        try:
            CapThreeFingers(design, "my_name2", options={})
        except Exception:
            self.fail("CapThreeFingers(design, \"my_name2\", options={})")

        try:
            CapThreeFingers(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "CapThreeFingers(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_qubits_transmon_concentric(self):
        """Test the instantiation of TransmonConcentric."""
        design = designs.DesignPlanar()
        try:
            TransmonConcentric
        except Exception:
            self.fail("TransmonConcentric failed")

        try:
            TransmonConcentric(design, "my_name")
        except Exception:
            self.fail("TransmonConcentric(design, \"my_name\") failed")

        try:
            TransmonConcentric(design, "my_name2", options={})
        except Exception:
            self.fail(
                "TransmonConcentric(design, \"my_name2\", options={}) failed")

        try:
            TransmonConcentric(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "TransmonConcentric(design, \"my_name3\", options={}, make=False)"
            )

    def test_qlibrary_qubits_transmon_cross(self):
        """Test the instantiation of TransmonCross."""
        design = designs.DesignPlanar()
        try:
            TransmonCross
        except Exception:
            self.fail("TransmonCross failed")

        try:
            TransmonCross(design, "my_name")
        except Exception:
            self.fail("TransmonCross(design, \"my_name\") failed")

        try:
            TransmonCross(design, "my_name2", options={})
        except Exception:
            self.fail("TransmonCross(design, \"my_name2\", options={}) failed")

        try:
            TransmonCross(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "TransmonCross(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_qubits_transmon_cross_fl(self):
        """Test the instantiation of TransmonCrossFL."""
        design = designs.DesignPlanar()
        try:
            TransmonCrossFL
        except Exception:
            self.fail("TransmonCrossFL failed")

        try:
            TransmonCrossFL(design, "my_name")
        except Exception:
            self.fail("TransmonCrossFL(design, \"my_name\") failed")

        try:
            TransmonCrossFL(design, "my_name2", options={})
        except Exception:
            self.fail(
                "TransmonCrossFL(design, \"my_name2\", options={}) failed")

        try:
            TransmonCrossFL(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "TransmonCrossFL(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_qubits_transmon_pocket(self):
        """Test the instantiation of TransmonPocket."""
        design = designs.DesignPlanar()
        try:
            TransmonPocket
        except Exception:
            self.fail("TransmonPocket failed")

        try:
            TransmonPocket(design, "my_name")
        except Exception:
            self.fail("TransmonPocket(design, \"my_name\") failed")

        try:
            TransmonPocket(design, "my_name2", options={})
        except Exception:
            self.fail("TransmonPocket(design, \"my_name2\", options={}) failed")

        try:
            TransmonPocket(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "TransmonPocket(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_qubits_transmon_pocket_cl(self):
        """Test the instantiation of TransmonPocketCL."""
        design = designs.DesignPlanar()
        try:
            TransmonPocketCL
        except Exception:
            self.fail("TransmonPocketCL failed")

        try:
            TransmonPocketCL(design, "my_name")
        except Exception:
            self.fail("TransmonPocketCL(design, \"my_name\") failed")

        try:
            TransmonPocketCL(design, "my_name2", options={})
        except Exception:
            self.fail(
                "TransmonPocketCL(design, \"my_name2\", options={}) failed")

        try:
            TransmonPocketCL(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "TransmonPocketCL(design, \"my_name3\", options={}, make=False)"
            )

    def test_qlibrary_qubits_transmon_pocket_6(self):
        """Test the instantiation of TransmonPocket6."""
        design = designs.DesignPlanar()
        try:
            TransmonPocket6
        except Exception:
            self.fail("TransmonPocket6 failed")

        try:
            TransmonPocket6(design, "my_name")
        except Exception:
            self.fail("TransmonPocket6(design, \"my_name\") failed")

        try:
            TransmonPocket6(design, "my_name2", options={})
        except Exception:
            self.fail(
                "TransmonPocket6(design, \"my_name2\", options={}) failed")

        try:
            TransmonPocket6(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "TransmonPocket6(design, \"my_name3\", options={}, make=False)")

    def test_qlibrary_qubits_tunable_coupler_01(self):
        """Test the instantiation of TunableCoupler01."""
        design = designs.DesignPlanar()
        try:
            TunableCoupler01
        except Exception:
            self.fail("TunableCoupler01 failed")

        try:
            TunableCoupler01(design, "my_name")
        except Exception:
            self.fail("TunableCoupler01(design, \"my_name\") failed")

        try:
            TunableCoupler01(design, "my_name2", options={})
        except Exception:
            self.fail(
                "TunableCoupler01(design, \"my_name2\", options={}) failed")

        try:
            TunableCoupler01(design, "my_name3", options={}, make=False)
        except Exception:
            self.fail(
                "TunableCoupler01(design, \"my_name3\", options={}, make=False)"
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
