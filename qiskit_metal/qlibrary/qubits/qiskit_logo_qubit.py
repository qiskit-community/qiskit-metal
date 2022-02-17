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
"""This is the QiskitLogoQubit module.
DISCLAIMER: This is a fun little Easter egg to portray the design capabilities of Metal! :D"""

from math import sin, cos, acos, asin, radians, degrees
from shapely.geometry import CAP_STYLE
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit


class QiskitLogoQubit(BaseQubit):
    """A single configurable circle with multiple pads.

    Inherits `BaseQubit` class.

    Create a circular transmon qubit with up to 3 connectors and one readout.

    .. image::
        qiskit_logo_qubit.png

    .. meta::
        Qiskit Logo Qubit

    Default Options:
        * pad_radius: "300um" -- Radius of the circle defining the qiskit logo shape
        * pad_gap: "20um" -- Gap between the two halves of qiskit logo shape
        * pad_logo_cutout_thickness: "10um" -- Thickness of the cutout in shunt-cap pads to make the Qsphere rings
        * pad_logo_cutout_margin: "20um" -- Margin in shunt-cap to avoid cutouts very near to the edge

        * connection_pads (default value: [trapezoid|ellipse]):
            * pad_location: "+1" -- Location of pad (+1 for [right|top], -1 for [left|bottom], 0 for [auto])
            * pad_width: ["80um"|"100um"] -- Width of the pad
            * pad_gap: "15um" -- Gap between the sunt-cap boundary and the coupling-pad
            * pad_depth: ["130um"|"15um"] -- Depth of connection pad inside shunt_cap boundary
            * pad_type: "ellipse" -- "ellipse" or "trapezoid" (max. 2 of each, total of 4 pads)
            * port_length: "60um" -- Length of the rectangular part of the connector
            * cpw_width: "10um" -- Width of the connector to CPW

        * resolution: "16" -- Resolution of the round cap design
        * subtract: "False"
        * helper: "False"
    """
    component_metadata = Dict(short_name="QiskitLogo",
                              _qgeometry_table_poly="True",
                              _qgeometry_table_junction="True")
    """Component metadata"""

    default_options = Dict(
        pad_radius="300um",
        pad_gap="20um",
        junc_width="20um",
        pad_logo_cutout_thickness="10um",
        pad_logo_cutout_margin="20um",
        _default_connection_pads=Dict(
            pad_location="0",
            pad_width="80um",
            pad_gap="15um",
            pad_depth="130um",
            pad_type="trapezoid", # ellipse, trapezoid
            port_length="60um",
            cpw_width="10um"),
        resolution="16",
        subtract="False",
        helper="False")
    """Default drawing options"""

    def _set_options_connection_pads(self):
        """Applies the default options."""
        super()._set_options_connection_pads()

        # TODO: Think of some better way to this
        for name in self.options.connection_pads:
            if self.options.connection_pads[name].pad_type == "ellipse":
                pw = self.options.connection_pads[name].pad_width[:-2]
                pd = self.options.connection_pads[name].pad_depth[:-2]
                if int(pw) < 100:
                    self.options.connection_pads[name].pad_width = "100um"
                if int(pd) > 30:
                    self.options.connection_pads[name].pad_depth = "15um"

    def make(self):
        """The make function implements the logic that creates the geometry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc.
        """
        self.make_qiskit_logo()
        self.make_couplers()
        self.make_outer_circle()

    def make_circle(self, radius):
        """This function creates the inner circle to be accessed later."""
        p = self.p

        # draw a circle
        circle = draw.Point(0, 0).buffer(radius,
                                         resolution=int(p.resolution),
                                         cap_style=getattr(CAP_STYLE, "round"))

        return circle

    def make_qsphere_state(self, radius, circ_pos_x, rot_angle):
        """This function creates the Qsphere state
                -- two circles + one line connecting them"""
        p = self.p

        # Some local variables
        # asin(1/11) === asin(0.1*p.radius / (p.radius + 0.1*p.radius))
        offset_angle = degrees(asin(p.pad_gap / (2*1.1*p.pad_radius)) + asin(1/11))

        # draw an ellipse
        circ1 = draw.Point(0, 0).buffer(radius,
                                       resolution=int(p.resolution),
                                       cap_style=getattr(CAP_STYLE, "round"))

        circ2 = draw.Point(0, 0).buffer(radius,
                                       resolution=int(p.resolution),
                                       cap_style=getattr(CAP_STYLE, "round"))

        # Two circles
        circ1 = draw.translate(circ1, circ_pos_x, 0)
        circ2 = draw.translate(circ2, -circ_pos_x, 0)

        # Rect for margin
        margin_rect = draw.rectangle(2*p.pad_radius-p.pad_logo_cutout_margin,
                                     p.pad_gap+2*p.pad_logo_cutout_margin)
        margin_rect = draw.rotate(margin_rect, rot_angle, origin=(0, 0))

        circ = draw.union(circ1, circ2)
        circ = draw.rotate(circ, rot_angle+offset_angle, origin=(0, 0))
        qsphere_state = draw.union(circ, margin_rect)

        gap_rect = draw.rectangle(2*p.pad_radius, p.pad_gap)
        gap_rect = draw.rotate(gap_rect, rot_angle, origin=(0, 0))

        return [qsphere_state, gap_rect]

    def get_trap_coords(self, base_width, top_width, height, gap_offset):
        coord_x1 = -(base_width + gap_offset)/2
        coord_x2 = (base_width + gap_offset)/2
        coord_x3 = (top_width + gap_offset)/2
        coord_x4 = -(top_width + gap_offset)/2
        coord_y1 = -height/2
        coord_y2 = height/2 + gap_offset/2

        return [(coord_x1, coord_y1),
                (coord_x2, coord_y1),
                (coord_x3, coord_y2),
                (coord_x4, coord_y2)]

    def make_trap_transformations(self, obj, translate_x, rot_angle, left_or_right, offset):
        trans_x_offset = translate_x-offset
        new_obj = draw.rotate(obj, left_or_right*90, origin=(0, 0))
        new_obj = draw.translate(new_obj, left_or_right*trans_x_offset, 0)
        new_obj = draw.rotate(new_obj, left_or_right*rot_angle, origin=(0, 0))
        return new_obj

    def get_ellipse_coords(self, angle_elev):
        """This function generates the required coordinates for an ellipse"""
        p = self.p

        ellipse_y_coord = p.pad_radius*sin(radians(angle_elev))
        ellipse_radius = p.pad_radius*cos(radians(angle_elev))
        ellipse_1_radius = ellipse_radius - p.pad_logo_cutout_margin
        ellipse_2_radius = ellipse_1_radius - 2*p.pad_logo_cutout_thickness

        return [ellipse_1_radius, ellipse_2_radius, ellipse_y_coord]

    def make_ellipse(self, radius, pos_y=0, y_scale=0.2):
        """This function makes an ellipse to be accessed later"""
        p = self.p

        # draw an ellipse
        circ = draw.Point(0, 0).buffer(radius,
                                       resolution=int(p.resolution),
                                       cap_style=getattr(CAP_STYLE, "round"))

        ellipse = draw.scale(circ, 1, y_scale)
        ellipse = draw.translate(ellipse, 0, pos_y)
        return ellipse

    def make_ellipse_ring(self, angle_elev, y_scale):
        """This function creates an elliptical ring to be accessed later"""
        [ell_1_radius, ell_2_radius, ell_pos_y] = self.get_ellipse_coords(angle_elev=angle_elev)
        ell_1 = self.make_ellipse(radius=ell_1_radius, pos_y=ell_pos_y)
        ell_2 = self.make_ellipse(radius=ell_2_radius, pos_y=ell_pos_y, y_scale=y_scale)
        ring = draw.subtract(ell_1, ell_2)
        return [ring, ell_1_radius, ell_pos_y]

    def make_qiskit_logo(self):
        """This function creates the Qiskit Logo mask"""
        p = self.p

        # Some local variables
        qsphere_state_angle = 55
        y_scale_factor = 0.18

        # Middle ring
        [ring_mid, ring_mid_radius, _] = self.make_ellipse_ring(angle_elev=0,
                                                                y_scale=y_scale_factor)
        # Upper ring
        [ring_upper, _, _] = self.make_ellipse_ring(angle_elev=30, y_scale=y_scale_factor)
        # Lower ring
        [ring_lower, ring_lower_radius, ring_lower_y] = self.make_ellipse_ring(angle_elev=-30,
                                                                               y_scale=y_scale_factor)
        logo_cutouts = draw.union(ring_mid, ring_upper, ring_lower)

        # Drawing mask for middle and lower rings
        # Middle ring mask
        y_translate_mid = ring_mid_radius*y_scale_factor
        rect_mask_mid = draw.rectangle(2*(p.pad_radius-p.pad_logo_cutout_margin),
                                       1.5*y_translate_mid,
                                       0,
                                       y_translate_mid*0.7)
        # Lower ring mask
        y_translate_lower = ring_lower_radius*y_scale_factor
        rect_mask_lower = draw.rectangle(2*(ring_lower_radius),
                                         1.2*y_translate_lower,
                                         0,
                                         y_translate_lower*0.6 + ring_lower_y)

        logo_masks = draw.union(rect_mask_lower, rect_mask_mid)

        # Drawing the qsphere state
        [qsphere_state, gap_rect] = self.make_qsphere_state(p.pad_radius*0.1,
                                                            p.pad_radius*1.08,
                                                            -qsphere_state_angle)

        # Josphson junction
        junction = draw.LineString([[0, -p.pad_gap/2], [0, p.pad_gap/2]])
        junction = draw.rotate(junction, -qsphere_state_angle, origin=(0, 0))

        # Make final logo
        logo = self.make_circle(p.pad_radius)
        logo = draw.subtract(logo, logo_cutouts)
        logo = draw.union(logo, logo_masks)
        logo = draw.union(logo, qsphere_state)
        logo = draw.subtract(logo, gap_rect)

        if len(p.connection_pads) > 0:
            coupler_cutouts = self.make_cutouts()
            for shp in coupler_cutouts:
                logo = draw.subtract(logo, shp)

        # Make final rotations and translations
        total = [logo, junction]
        total = draw.rotate(total, p.orientation, origin=(0, 0))
        total = draw.translate(total, p.pos_x, p.pos_y)
        [logo, junction] = total

        self.add_qgeometry("poly", {"qiskit_logo": logo},
                           layer=p.layer,
                           chip=p.chip)

        self.add_qgeometry("junction", {"jj": junction},
                           width=p.junc_width,
                           layer=p.layer,
                           chip=p.chip)

    def make_ellipse_coupler(self, num_ell, conn_pad, offset, is_cutout=True):
        """This function creates a ellipse coupler/cutout to be used later"""
        p = self.p

        elevation_angle = degrees(acos(conn_pad.pad_width / p.pad_radius))
        [ell_radius, _, ell_pos_y] = self.get_ellipse_coords(elevation_angle)
        ell_radius += offset
        if conn_pad.pad_location == 0.0:
            up_or_down = (num_ell%2)*2 - 1
        else:
            up_or_down = conn_pad.pad_location

        y_scale_factor = 0.25 if is_cutout else 0.2
        ell_pos_y = ell_pos_y-conn_pad.pad_depth
        ell = self.make_ellipse(radius=ell_radius,
                                pos_y=up_or_down*ell_pos_y,
                                y_scale=y_scale_factor)

        rect_height = p.pad_radius - ell_pos_y + conn_pad.port_length
        rect = draw.rectangle(4*conn_pad.cpw_width + offset,
                              rect_height,
                              0,
                              up_or_down*(ell_pos_y+rect_height/2))

        total_ell = draw.union(ell, rect)

        if not is_cutout:
            # Make pin coords
            pin_in = (0, up_or_down*p.pad_radius)
            pin_out = (0, up_or_down*(p.pad_radius + conn_pad.port_length))
            pin = draw.LineString([pin_in, pin_out])
            return [total_ell, pin]

        return total_ell

    def make_trap_coupler(self, num_trap, conn_pad, offset, is_cutout=True):
        """This function creates a trapezoid coupler/cutout to be used later"""
        p = self.p

        trap_coords = self.get_trap_coords(conn_pad.pad_width,
                                           conn_pad.pad_width/2,
                                           conn_pad.pad_depth,
                                           offset)
        trap = draw.Polygon(trap_coords)
        if conn_pad.pad_location == 0.0:
            left_or_right = (num_trap%2)*2 - 1
        else:
            left_or_right = conn_pad.pad_location

        rect_y = -(conn_pad.port_length/2 - trap_coords[0][1])
        rect = draw.rectangle(4*conn_pad.cpw_width, conn_pad.port_length, 0, rect_y)

        total_trap = draw.union(trap, rect)

        if not is_cutout:
            # Make pin coords
            pin_in = (0, trap_coords[0][1])
            pin_out = (0, (trap_coords[0][1] - conn_pad.port_length))
            pin = draw.LineString([pin_in, pin_out])
            objs = [total_trap, pin]
            objs = self.make_trap_transformations(objs,
                                                  p.pad_radius,
                                                  15,
                                                  left_or_right,
                                                  conn_pad.pad_depth/2)
            return objs

        total_trap = self.make_trap_transformations(total_trap,
                                              p.pad_radius,
                                              15,
                                              left_or_right,
                                              conn_pad.pad_depth/2)
        return total_trap

    def get_num_couplers(self):
        pc = self.p.connection_pads

        cutout_types = [pc[name].pad_type for name in self.options.connection_pads]
        num_ell_cutouts = cutout_types.count("ellipse")
        num_trap_cutouts = len(cutout_types) - num_ell_cutouts

        if num_ell_cutouts > 2 or num_trap_cutouts > 2:
            self.logger.info(f"This qubit can have maximum 2 couplers for each 'ellipse' and 'trapezoid' type. Found more than two.")

        return [num_ell_cutouts, num_trap_cutouts]

    def make_cutouts(self):
        """This function creates cutouts for couplers"""
        pc = self.p.connection_pads

         # Initial sanity check and
         # get number of coupleres for each type
        [num_ell_cutouts, num_trap_cutouts] = self.get_num_couplers()

        # Make the shapes
        cutouts_list = []
        for name in self.options.connection_pads:
            conn_pad = pc[name]
            if conn_pad.pad_type == "ellipse" and num_ell_cutouts > 0:
                ell_cutout = self.make_ellipse_coupler(num_ell_cutouts, conn_pad, conn_pad.pad_gap)
                num_ell_cutouts -= 1
                cutouts_list.append(ell_cutout)

            elif conn_pad.pad_type == "trapezoid" and num_trap_cutouts > 0:
                trap_cutout = self.make_trap_coupler(num_trap_cutouts, conn_pad, conn_pad.pad_gap)
                num_trap_cutouts -= 1
                cutouts_list.append(trap_cutout)

            else:
                self.logger.info(f"Expected pad_type to be either 'ellipse' or 'trapezoid', found '{conn_pad.pad_type}'.")

        return cutouts_list

    def make_couplers(self):
        """This function creates the respective couplers"""
        pc = self.p.connection_pads

         # Initial sanity check and
         # get number of coupleres for each type
        [num_ell_couplers, num_trap_couplers] = self.get_num_couplers()

        # Make the shapes
        couplers_list = []
        for name in self.options.connection_pads:
            conn_pad = pc[name]
            if conn_pad.pad_type == "ellipse" and num_ell_couplers > 0:
                ell_coupler_pin = self.make_ellipse_coupler(num_ell_couplers, conn_pad, 0, False)
                num_ell_couplers -= 1
                couplers_list.append(ell_coupler_pin)

            elif conn_pad.pad_type == "trapezoid" and num_trap_couplers > 0:
                trap_coupler_pin = self.make_trap_coupler(num_trap_couplers, conn_pad, 0, False)
                num_trap_couplers -= 1
                couplers_list.append(trap_coupler_pin)

            else:
                self.logger.info(f"Expected pad_type to be either 'ellipse' or 'trapezoid', found '{conn_pad.pad_type}'.")

        couplers_list = draw.rotate(couplers_list, self.p.orientation, origin=(0, 0))
        couplers_list = draw.translate(couplers_list, self.p.pos_x, self.p.pos_y)

        for i,name in enumerate(self.options.connection_pads):
            self.add_qgeometry("poly", {name+"_connector_pad": couplers_list[i][0]},
                               chip=self.p.chip,
                               layer=self.p.layer)
            self.add_pin(name,
                         couplers_list[i][1].coords,
                         width=pc[name].cpw_width,
                         input_as_norm=True)

    def make_outer_circle(self):
        """This function creates outer circle with subtract"""
        p = self.p
        pc = self.p.connection_pads

        port_lengths = [pc[name].port_length for name in self.options.connection_pads]
        max_port_length = 0
        if len(port_lengths) > 0:
            max_port_length = max(port_lengths)

        outer_radius = (p.pad_radius + max_port_length) + p.pad_logo_cutout_margin

        # check if outer radius is still smaller than
        # the qsphere state circles
        if outer_radius < 1.2*p.pad_radius:
            outer_radius = 1.2*p.pad_radius + p.pad_logo_cutout_margin

        outer_circle = self.make_circle(outer_radius)
        outer_circle = draw.rotate(outer_circle, self.p.orientation, origin=(0, 0))
        outer_circle = draw.translate(outer_circle, self.p.pos_x, self.p.pos_y)


        self.add_qgeometry("poly", {"outer_circle": outer_circle},
                           chip=p.chip,
                           layer=p.layer,
                           subtract=True)
