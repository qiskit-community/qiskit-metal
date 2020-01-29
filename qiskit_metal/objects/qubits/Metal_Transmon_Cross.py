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


'''
@date: 2019/09/08
@author: Thomas McConkey
'''

# Imports required for drawing
from copy import deepcopy
from shapely.geometry import LineString

from ...config import DEFAULT_OPTIONS, DEFAULT
from ...draw_functions import shapely, shapely_rectangle, translate, translate_objs,\
    rotate_objs, rotate_obj_dict, scale_objs, _angle_Y2X, make_connector_props,\
    Polygon, buffer,\
    Dict, draw_objs
from ... import draw_hfss
from .Metal_Qubit import Metal_Qubit
from shapely.ops import cascaded_union
from shapely.geometry import shape

# Connector default options
DEFAULT_OPTIONS['Metal_Transmon_Cross.connectors'] = Dict(
    connector_type='0', #0 = Claw type, 1 = gap type
    claw_length='30um',
    ground_spacing='5um',
    claw_width=DEFAULT_OPTIONS.cpw.width,
    claw_gap=DEFAULT_OPTIONS.cpw.gap,
    connector_location='0' #0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
)

#
DEFAULT_OPTIONS['Metal_Transmon_Cross'] = deepcopy(
    DEFAULT_OPTIONS['Metal_Qubit'])
DEFAULT_OPTIONS['Metal_Transmon_Cross'].update(Dict(
    pos_x='0um',
    pos_y='0um',
    cross_width='20um',
    cross_length='200um',
    cross_gap='20um',
    orientation='0',  # 90 has the SQUID on the X axis, while 0 has the SQUID on the Y axis
    #BETTER ROTATION NEEDED

    _hfss=Dict(
        rect_options=dict(color=DEFAULT['col_in_cond'],
                          transparency=0),  # default options for a rectangle
        BC_name_pads='qubit_cross',
        BC_name_conn='qubit_connectors',
        mesh_name='qubit_pockets',
        mesh_name_jj='qubit_jjs',
        mesh_name_pad='qubit_cross',
        mesh_name_conn='qubit_connectors',
        mesh_kw=Dict(MaxLength='20 um'),
        mesh_kw_jj=Dict(MaxLength='7um'),
        mesh_kw_pad=Dict(MaxLength='20um'),
        mesh_kw_con=Dict(MaxLength='35um'),
        Lj='Lj_0',
        Cj=0,                    # Warning - do not use non zero for pyEPR analsys
        _Rj=0,                    # Warning - do not use non zero for pyEPR analsys
        category='qubits',
        chip='main',               # which chip does qubit belong to
        mesh_pocket='10um',              # How much to mesh the pokcet beyond
    ),

    _gds=Dict(

    ),
))


class Metal_Transmon_Cross(Metal_Qubit):  # pylint: disable=invalid-name
    '''
Description:
    ----------------------------------------------------------------------------
    Simple Metal Transmon Cross object. Creates the A cross-shaped island,
    the "junction" on the south end, and up to 3 connectors on the remaining arms
    (claw or gap).

    'claw_width' and 'claw_gap' define the width/gap of the CPW line that
    makes up the connector. Note, DC SQUID currently represented by single
    inductance sheet

    Add connectors on it using the `options_connectors` dictonary.

    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Main Body
    ----------------------------------------------------------------------------
        pos_x / pos_y - where the center of the Crossmon should be located on chip
        cross_width - width of the CPW center trace making up the Crossmon
        cross_length - length of one Crossmon arm (from center)
        cross_gap - width of the CPW gap making up the Crossmon
        orientation - how to orient the qubit and connectors in the end (where the +X vector should point, '+X', '-X','+Y','-Y')

    Connectors
    ----------------------------------------------------------------------------
        connectorType - string of 'Claw' or 'Gap' to define which type of connector is used.
        claw_length - length of the claw 'arms', measured from the connector center trace
        ground_spacing - amount of ground plane between the connector and Crossmon arm (minimum should be based on fabrication capabilities)
        claw_width - the width of the CPW center trace making up the claw/gap connector
        claw_gap - the gap of the CPW center trace making up the claw/gap connector
        connector_location - string of 'W', 'N', or 'E', which of the three arms where a given connector should be (South is for the junction)

    Sketch
    ----------------------------------------------------------------------------
                        claw_length
    Claw:       _________                    Gap:
                |   ________________             _________    ____________
          ______|  |                             _________|  |____________
                |  |________________
                |_________

    '''
    _img = 'Metal_Crossmon.png'
    # TO DO:
    # * Add DC SQUID structure (maybe as an option, only for GDS?)
    # * HFSS drawing mesh

##############################################MAKE################################################################################
    def make(self):
        self.make_pocket()
        self.make_connectors()


###################################TRANSMON###########################################################################################


    def make_pocket(self):
        '''
        Makes a basic Crossmon, 4 arm cross.
        '''
        options = self.options

        # First grabs the various option values.
        cross_width, cross_length, cross_gap,\
            pos_x, pos_y, orientation = self.design.get_option_values(options, 'cross_width,\
                 cross_length, cross_gap, pos_x, pos_y, orientation')

        # Then starts drawing the cross using the above values.
        # Vertical and Horizontal rectangles, and the 'etch' section which generates the gap (should have just used buffer, owell)
        cross_ArmGapV = shapely.geometry.box(-(cross_width/2+cross_gap), -
                                             cross_length-cross_gap, (cross_width/2+cross_gap), cross_length+cross_gap)
        cross_ArmV = shapely.geometry.box(-cross_width/2, -
                                          cross_length, cross_width/2, cross_length)

        cross_ArmGapH = shapely.geometry.box(-cross_length - cross_gap, -(
            cross_width/2+cross_gap), cross_length+cross_gap, (cross_width/2+cross_gap))
        cross_ArmH = shapely.geometry.box(-cross_length, -
                                          cross_width/2,  cross_length, cross_width/2)

        cross_Etcher = cascaded_union([cross_ArmGapH, cross_ArmGapV])
        cross_Island = cascaded_union([cross_ArmH, cross_ArmV])

        # The Junction (Should be the DC SQUID in future?)
        rect_jj = shapely_rectangle(cross_width, cross_gap)
        rect_jj = translate(rect_jj, 0, -cross_length-cross_gap/2)

        objects = dict(
            rect_jj=rect_jj,
            cross_Island=cross_Island,
            cross_Etcher=cross_Etcher,
        )

        # Rotate and translate Crossmon
        objects = rotate_obj_dict(objects, orientation, origin=(0, 0))
        objects = translate_objs(objects, pos_x, pos_y)

        self.objects.update(objects)

        return objects

############################CONNECTORS##################################################################################################
    def make_connectors(self):
        '''
        Goes through connectors and makes each one.
        '''
        for name, options_connector in self.options.connectors.items():
            ops = deepcopy(DEFAULT_OPTIONS['Metal_Transmon_Cross.connectors'])
            ops.update(options_connector)
            options_connector.update(ops)
            self.make_connector(name, options_connector)

    def make_connector(self, name, options_connector):
        '''
        Makes individual connector

        Args:
        -------------
        name (str) : Name of the connector
        '''

        # Transmon options
        options = self.options  # for transmon
        cross_width, cross_length, cross_gap,\
            pos_x, pos_y, orientation = self.design.get_option_values(options, 'cross_width,\
                 cross_length, cross_gap, pos_x, pos_y, orientation')

        # Connector options
        #connector_type = options['connector_type,']
        #connector_location = options_connector['connector_location']
        claw_gap, claw_length, claw_width, ground_spacing, connector_type, connector_location = self.design.get_option_values(
            options_connector, 'claw_gap, claw_length, claw_width, ground_spacing, connector_type, connector_location')

        # Building the connector structure. Different construction based on connector type
        # (***match any changes to the port_Line)
        clawCPW = shapely.geometry.box(0, -claw_width/2, -4*claw_width, claw_width/2)

        if connector_type == 0: #Claw connector
            TEMP_clawHeight = 2*claw_gap + 2 * claw_width + 2 * \
                ground_spacing + 2*cross_gap + cross_width  # temp value

            clawBase = shapely.geometry.box(-claw_width, -
                                            (TEMP_clawHeight)/2, claw_length, TEMP_clawHeight/2)
            clawSubtract = shapely.geometry.box(
                0, -TEMP_clawHeight/2 + claw_width, claw_length, TEMP_clawHeight/2 - claw_width)
            clawBase = clawBase.difference(clawSubtract)

            connector_Arm = cascaded_union([clawBase, clawCPW])
            connector_Etcher = buffer(connector_Arm, claw_gap)
        else:
            connector_Arm = clawCPW
            connector_Etcher = buffer(connector_Arm, claw_gap)

        #Making the connector 'port' for design.connector tracking (for easy connect functions). Done here so
        #as to have the same translations and rotations as the connector. Could extract from the connector later, but since
        #allowing different connector types, this seems more straightforward.
        port_Line = shapely.geometry.LineString([(-4*claw_width,-claw_width/2),(-4*claw_width,claw_width/2)])

        # Store connector in object dictionary
        objects = dict(
            connector_Arm=connector_Arm,
            connector_Etcher=connector_Etcher,
            port_Line=port_Line,
        )

        # Moves to west arm before any rotations.
        objects = translate_objs(
            objects, -(cross_length + cross_gap + ground_spacing + claw_gap), 0)

        clawRotate = 0
        if connector_location>135:
            clawRotate = 180
        elif connector_location>45:
            clawRotate = -90

        # Rotates to the appropriate arm, then rotate and translate to match the rotation/position of the Crossmon
        objects = rotate_objs(objects, clawRotate, origin=(0, 0))

        objects = rotate_obj_dict(objects, orientation, origin=(0, 0))
        objects = translate_objs(objects, pos_x, pos_y)


        #Creating of the connection port for functions such as 'easy connect'. Uses the start and end point of the
        #port_line line, and generates a normal vector (vNorm) pointing in the direction any connection should be (eg. away from the Crossmon)
        #Not been fully tested with all potential variations.
        design = self.design
        if not design is None:
            portPoints = list(shape(objects['port_Line']).coords)
            vNorm = (-(portPoints[1][1] - portPoints[0][1]),(portPoints[1][0]-portPoints[0][0]))
            design.connectors[self.name+'_'+name] = make_connector_props(portPoints,options, vec_normal=vNorm)

        # Removes the temporary port_Line from draw objects
        del objects['port_Line']
        # add to objects
        self.objects.connectors[name] = objects

        return objects

##################################################################################################################
    # To draw the shape into HFSS, setup meshses, boundaries, etc.
    def hfss_draw(self):
        '''
        Draw in HFSS.
        Makes a meshing recntalge for the the pocket as well.
        '''

        # custom shortcuts (needs cleaning up)
        design = self.design
        name = self.name
        options = self.options
        options_hfss = self.options._hfss
        rect_options = options_hfss.rect_options
        _, oModeler = design.get_modeler()  # pylint: disable=invalid-name
        #def oh(x): return parse_units_user(options_hfss[x])  # pylint: disable=invalid-name

        # Make mesh objects
        rect_msh = self.objects.cross_Etcher

        # list of objects to draw in HFSS
        objs = [self.objects, dict(mesh=rect_msh)]

        # Pocket: Draw all pocket objects
        self.objects_hfss = Dict(draw_hfss.draw_objects_shapely(
            design.oModeler, objs, self.name, pos_z=self.get_chip_elevation(), hfss_options=rect_options))

        hfss_objs = self.objects_hfss  # shortcut

        # Pocket: Subtract ground - Uses "etcher shapes" to cut away sections of ground that need to be removed for the design.
        # Check the object names match to the shapes that should be 'etched'
        ground = design.get_ground_plane(options)
        oModeler.subtract(ground, [hfss_objs['cross_Etcher']])
        subtracts = [hfss_objs.connectors[xx]['connector_Etcher']
                     for xx in self.objects.connectors]
        oModeler.subtract(ground, subtracts)

        # CODE BLOCK FOR ASSIGNING Perfecet Electric Boundary ('superconductor thin film')
        if DEFAULT['do_PerfE']:
            oModeler.append_PerfE_assignment(name+'_cross' if DEFAULT['BC_individual'] else options_hfss['BC_name_pads'],
                                             hfss_objs['cross_Island'])

            for key in self.options.connectors:
                oModeler.append_PerfE_assignment(name+'_conn' if DEFAULT['BC_individual'] else options_hfss['BC_name_conn'],
                                                 [hfss_objs.connectors[key]['connector_Arm']])

        # CODE BLOCK FOR MAKING THE JUNCTIONS - check to make sure naming schemes are compatible
        # JJ line and Lumped RLC
        if 1:
            rect_jj = hfss_objs['rect_jj']  # pylint: disable=invalid-name # pyEPR.hfss.Rect
            axis= self.options.orientation
            axis = {90:'x',-90:'x',0:'y',180:'y'}.get(axis,axis)
            axis = axis.lower()
            rect_jj.make_rlc_boundary(axis, l=options_hfss['Lj'],
                                      c=options_hfss['Cj'], r=options_hfss['_Rj'],
                                      name='Lj_'+name)

            [start, end] = rect_jj.make_center_line(axis)

            poly_jj = oModeler.draw_polyline([start, end], closed=False,
                                             **{**rect_options, **dict(color=(128, 0, 128))})
            poly_jj = poly_jj.rename('JJ_'+name+'_')
            poly_jj.show_direction = True

        # CODE BLOCK FOR MESH OPERATIONS - Work in progress (optimal initial mesh locations TBD)
        if DEFAULT._hfss.do_mesh:

            # Pocket - trying to only mesh the gap but having some drawing issues.
            rect_mesh = hfss_objs['mesh']
            rect_mesh.wireframe = True
            design.mesh_obj(
                rect_mesh, options_hfss['mesh_name'], **options_hfss['mesh_kw'])

        return hfss_objs
