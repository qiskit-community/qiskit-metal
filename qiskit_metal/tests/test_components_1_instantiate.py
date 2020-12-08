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

#pylint: disable-msg=unnecessary-pass
#pylint: disable-msg=too-many-public-methods
#pylint: disable-msg=broad-except
"""
Qiskit Metal unit tests components functionality.

Created on Wed Apr 22 09:58:35 2020
@author: Jeremy D. Drysdale
"""

import unittest
from PySide2.QtWidgets import QColorDialog

from qiskit_metal.components.base.base import QComponent
from qiskit_metal.components.base.qroute import QRoute
from qiskit_metal.components.base.qroute import QRouteLead
from qiskit_metal.components.base.qroute import QRoutePoint
from qiskit_metal.components.base.qubit import BaseQubit
from qiskit_metal.components.basic.circle_caterpillar import CircleCaterpillar
from qiskit_metal.components.basic.circle_raster import CircleRaster
from qiskit_metal.components.basic.rectangle import Rectangle
from qiskit_metal.components.basic.rectangle_hollow import RectangleHollow
from qiskit_metal.components.basic.n_gon import NGon
from qiskit_metal.components.basic.n_square_spiral import NSquareSpiral
from qiskit_metal.components.connectors.cpw_hanger_t import CPWHangerT
from qiskit_metal.components.connectors.open_to_ground import OpenToGround
from qiskit_metal.components.connectors.short_to_ground import ShortToGround
from qiskit_metal.components.interconnects.anchored_path import RouteAnchors
from qiskit_metal.components.interconnects.framed_path import RouteFramed
from qiskit_metal.components.interconnects.straight_path import RouteStraight
from qiskit_metal.components.interconnects.pathfinder import RoutePathfinder
from qiskit_metal.components.interconnects.meandered import RouteMeander
from qiskit_metal.components.interconnects.mixed_path import RouteMixed
from qiskit_metal.components.passives.launchpad_wb import LaunchpadWirebond
from qiskit_metal.components.passives.launchpad_wb_coupled import LaunchpadWirebondCoupled
from qiskit_metal.components.passives.cap_three_fingers import CapThreeFingers
from qiskit_metal import designs
from qiskit_metal.components._template import MyQComponent
from qiskit_metal.tests.assertions import AssertionsMixin
from qiskit_metal.toolbox_python.metal_exceptions import ComponentInitFailedError
#pylint: disable-msg=line-too-long
from qiskit_metal.components.interconnects.resonator_rectangle_spiral import ResonatorRectangleSpiral


class TestComponentInstantiation(unittest.TestCase, AssertionsMixin):
    """
    Unit test class
    """

    ## Tests with make implemented
    def qcomponent_implemented_make_true(self, component_class, component_name):
        """ Tests whether the class creates a build when called except when make=False (should create except when make=False).
        Also tests whether ComponentInitFailedError is thrown in the event you try
        to instantiate a component with the same name as a pre-existing component

        Args:
            component_class (Class): Any Class inheriting from QComponent that has an implemented `make` method
            component_name ([type]): String of the name of the class
        """
        design = designs.DesignPlanar()

        try:
            component_class
        except Exception:
            self.fail(f"{component_name} failed")

        try:
            c1 = component_class(design, "my_name")
            #self.assertTrue(c1._made)
        except Exception as e:
            self.fail(e)

        c2 = component_class(design, "my_name2", options={})
        self.assertTrue(c2._made)

        c3 = component_class(design, "my_name3", options={}, make=False)
        self.assertFalse(c3._made)

        with self.assertRaises(
                ComponentInitFailedError
                #should fail trying to make a new component_class with the same name as a previous component_class
        ) as cm:
            component_class(design, "my_name")
        self.assertIn("Cannot create component. Name", str(cm.exception))

        design.delete_all_components()

    def test_component_instantiate_basequbit(self):
        self.qcomponent_implemented_make_true(BaseQubit, "BaseQubit")

    def test_component_instantiate_open_to_ground(self):
        self.qcomponent_implemented_make_true(OpenToGround, "OpenToGround")

    def test_component_instantiate_short_to_ground(self):
        self.qcomponent_implemented_make_true(ShortToGround, "ShortToGround")

    def test_component_instantiate_cpw_hanger_t(self):
        self.qcomponent_implemented_make_true(CPWHangerT, "CPWHangerT")

    def test_component_instantiate_resonator_rectangle_spiral(self):
        self.qcomponent_implemented_make_true(ResonatorRectangleSpiral,
                                              "ResonatorRectangleSpiral")

    def test_component_instantiate_circle_raster(self):
        self.qcomponent_implemented_make_true(CircleRaster, "CircleRaster")

    def test_component_instantiate_circle_caterpillar(self):
        self.qcomponent_implemented_make_true(CircleCaterpillar,
                                              "CircleCaterpillar")

    def test_component_instantiate_n_gon(self):
        self.qcomponent_implemented_make_true(NGon, "NGon")

    def test_component_instantiate_n_square_spiral(self):
        self.qcomponent_implemented_make_true(NSquareSpiral, "NSquareSpiral")

    def test_component_instantiate_rectangle(self):
        self.qcomponent_implemented_make_true(Rectangle, "Rectangle")

    def test_component_instantiate_rectangle_hollow(self):
        self.qcomponent_implemented_make_true(RectangleHollow,
                                              "RectangleHollow")

    def test_component_instantiate_launch_v1(self):
        self.qcomponent_implemented_make_true(LaunchpadWirebond,
                                              "LaunchpadWirebond")

    def test_component_instantiate_launch_v2(self):
        self.qcomponent_implemented_make_true(LaunchpadWirebondCoupled,
                                              "LaunchpadWirebondCoupled")

    def test_component_instantiate_three_finger_cap_v1(self):
        self.qcomponent_implemented_make_true(CapThreeFingers,
                                              "CapThreeFingers")

    ## Tests QComponent without make implemented
    def qcomponent_implemented_make_false(self, component_class,
                                          component_name):
        """ Tests whether the class creates a build when called (should not create build).
        Also tests whether ComponentInitFailedError is thrown in the event you try
        to instantiate a component with the same name as a pre-existing component

        Args:
            component_class (Class): Any Class inheriting from QComponent that does NOT have an implemented `make` method
            component_name ([type]): String of the name of the class
        """
        design = designs.DesignPlanar()

        try:
            component_class
        except Exception:
            self.fail(f"{component_name} failed")

        c1 = component_class(design, "my_name")
        self.assertFalse(c1._made)

        c2 = component_class(design, "my_name2", options={})
        self.assertFalse(c2._made)

        c3 = component_class(design, "my_name3", options={}, make=False)
        self.assertFalse(c3._made)

        with self.assertRaises(
                ComponentInitFailedError
                #should fail trying to make a new component_class with the same name as a previous component_class
        ) as cm:
            component_class(design, "my_name")
        self.assertIn("Cannot create component. Name", str(cm.exception))

        design.delete_all_components()

    def test_component_instantiate_basequbit(self):
        self.qcomponent_implemented_make_false(BaseQubit, "BaseQubit")

    def test_component_instantiate_qcomponent(self):
        self.qcomponent_implemented_make_false(QComponent, "QComponent")

    #QRoute Tests
    # Should fail because there are no valid pins
    def qcomponent_instantiate_routes_exception(self, component_class,
                                                component_name):
        design = designs.DesignPlanar()

        with self.assertRaises(
                ComponentInitFailedError
                #should fail trying to make a new component_class with the same name as a previous component_class
        ) as cm:
            component_class(design, "my_name")
        self.assertIn("Cannot create component due to pin errors",
                      str(cm.exception))

        with self.assertRaises(
                ComponentInitFailedError
                #should fail trying to make a new component_class with the same name as a previous component_class
        ) as cm:
            component_class(design, "my_name", options={})
        self.assertIn("Cannot create component due to pin errors",
                      str(cm.exception))

        with self.assertRaises(
                ComponentInitFailedError
                #should fail trying to make a new component_class with the same name as a previous component_class
        ) as cm:
            component_class(design, "my_name", options={}, make=False)
        self.assertIn("Cannot create component due to pin errors",
                      str(cm.exception))

        design.delete_all_components()

    def test_component_instantiate_route_straight(self):
        self.qcomponent_instantiate_routes_exception(RouteStraight,
                                                     "RouteStraight")

    def test_component_instantiate_route_anchors(self):
        self.qcomponent_instantiate_routes_exception(RouteAnchors,
                                                     "RouteAnchors")

    def test_component_instantiate_route_pathfinder(self):
        self.qcomponent_instantiate_routes_exception(RoutePathfinder,
                                                     "RoutePathfinder")

    def test_component_instantiate_route_meander(self):
        self.qcomponent_instantiate_routes_exception(RouteMeander,
                                                     "RouteMeader")

    ## Special Tests

    def test_component_instantiate_route_frame_path(self):
        """
        Test the instantiation of RouteFramed
        """
        try:
            RouteFramed
        except Exception:
            self.fail("RouteFramed failed")

    def test_component_instantiate_q_route_lead(self):
        """
        Test the instantiation of QRouteLead
        """
        try:
            QRouteLead
        except Exception:
            self.fail("QRouteLead failed")

    def test_component_instantiate_q_route_point(self):
        """
        Test the instantiation of QRoutePoint
        """
        try:
            QRoutePoint
        except Exception:
            self.fail("QRoutePoint failed")

    def test_component_instantiate_route_meander(self):
        """
        Test the instantiation of RouteMeander
        """
        try:
            RouteMeander
        except Exception:
            self.fail("RouteMeander failed")

    def test_component_instantiate_route_mixed(self):
        """
        Test the instantiation of RouteMixed
        """
        try:
            RouteMixed
        except Exception:
            self.fail("RouteMixed failed")

    def test_component_instantiate_q_route(self):
        """
        Test the instantiation of QRoute
        """
        try:
            QRoute
        except Exception:
            self.fail("QRoute failed")


if __name__ == '__main__':
    unittest.main(verbosity=2)
