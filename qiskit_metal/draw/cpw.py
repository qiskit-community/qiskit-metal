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
Function to draw CPW geometries.

TODO: CREATE A PROPER PATH CLASS.

@author: Zlatko K. Minev, 2019
'''

import ast
import numpy as np
import matplotlib.pyplot as plt
import shapely

from numpy import sqrt, pi, array, flip
from numpy.linalg import norm
from shapely.geometry import Point, Polygon, LineString, CAP_STYLE, JOIN_STYLE

from .. import DEFAULT, DEFAULT_OPTIONS, Dict, logger, draw
from ..toolbox_metal.parsing import  parse_value, TRUE_STR
from .utility import vec_add_z,\
    vec_unit_norm, vec_unit_planar,\
    remove_colinear_pts
from .basic import flip_merge, rotate_position
from .utility import * #this import out of date given new folder structure?



##############################################################################
###
###  CPW BASIC DRAWING
###
#NEEDS UPDATING FOR ELEMENTS AND RENDERER - bunch should be in renderer_ansys
DEFAULT_OPTIONS['draw_cpw_trace'] = {
    'func_draw'           : 'draw_cpw_trace',
    'chip'                : 'main',
    'name'                : 'CPW1',         # Name of the line
    'trace_center_width'  : DEFAULT_OPTIONS.cpw.width,         # Center trace width
    'trace_center_gap'    : DEFAULT_OPTIONS.cpw.gap,
    'trace_mesh_gap'      : DEFAULT_OPTIONS.cpw.mesh_width,          # For mesh rectangle
    'fillet'              : DEFAULT_OPTIONS.cpw.fillet,        # Fillt
    'ground_plane'        : 'ground_plane', # name of ground plane to subtract from, maybe make also automatic
    'do_only_lines'       : 'False',        # only draw the lines
    'do_mesh'             :  DEFAULT._hfss.do_mesh,  # Draw trace for meshing
    'do_subtract_ground'  : 'True',         # subtract from ground plane
    'do_sub_keep_original': 'False',        # keep_originals when perfomring subtraction
    'do_assign_perfE'     :  True,
    'BC_individual'       :  False,
    'BC_name'             : 'CPW_center_traces',
    'category'            : 'cpw',
    'do_add_connectors'   :  True,
    'units'               : 'mm',           # default units
    'poly_default_options': {'transparency':0.95, 'color':DEFAULT['col_in_cond']}, # dictionary 100,120,90
    'mesh_name'           : 'cpw',
    'mesh_kw'             : Dict(MaxLength='0.1mm')
}

def draw_cpw_trace(design,
                   points,
                   options = {},
                   category = 'CPW',
                   name = None
                  ):
    '''
        points : 2D List assumed in USER units.
    '''
    _, oModeler = design.get_modeler()
    to_vec3D = lambda vec: draw.vec_add_z(vec, design.get_chip_z(options['chip']))

    options  = {**DEFAULT_OPTIONS['draw_cpw_trace'], **options} # update with custom options
    poly_default_options = options['poly_default_options']

    ### Paramaters
    if name == None:
        name = options['name']
    fillet, cpw_center_w, cpw_center_gap_dt = parse_value_hfss(design.get_option_values(options,
                  'fillet, trace_center_width, trace_mesh_gap'))
    trace_mesh_gap_dt = cpw_center_gap_dt

    cpw_center_gap = cpw_center_w   + 2*cpw_center_gap_dt   # total width of sweep line
    cpw_mesh_gap   = cpw_center_gap + 2*trace_mesh_gap_dt   # total width of sweep line

    ### POINTS / UNITS
    # add units, parse, and  enforce numpy array
    #list_units = lambda array, unit=options['units']: np.array(list(map(lambda x: parse_entry(str(x)+unit),array)))
    points     = parse_units(points) #list(map(list_units, points))
    cpw_origin = points[0]
    vec_D, vec_d, vec_n = vec_unit_norm([points[0], points[1]]) # distance vector, unit dist. vector, normal unit vector

    ### Make Polyline
    def make_obj_polyline_track(name, swp_w, poly_default_options=poly_default_options):
        obj_poly_track = oModeler.draw_polyline(to_vec3D(points), closed=False,
                                                name=name+'_track',
                                                **poly_default_options)
        dist = swp_w/2.*vec_n
        obj_poly_swp = oModeler.draw_polyline(to_vec3D([cpw_origin-dist, cpw_origin+dist]), closed=False,
                                                name=name,
                                                **poly_default_options)
        if not fillet in [0, 0.0]:
            #TODO: add something about the verteces which get filled as an option
            # TODO: Make thif fillet routine a function
            # do not fillet pointif the distanc eon either side of it is too small for fillet
            do_not_fillet = []
            for i in range(1, len(points)-1):
                dist = lambda p1,p2: abs(norm(array(points[p1])-array(points[p2])))
                #print('Fillet:', fillet, dist(i,i-1), dist(i,i+1), points[i], points[i+1])
                if (dist(i,i-1) <= fillet) or (dist(i,i+1) <= fillet):
                    logger.debug(f'Fillet [name={name}][i={i}][ len(points)-1= {len(points)-1}]:\ndist(i,i-1), dist(i,i+1), 2*fillet = {1000*np.array([dist(i,i-1), dist(i,i+1), 2*fillet])}')
                    do_not_fillet += [i]
                if len(do_not_fillet)>0:
                    pass #print('print(do_not_fillet)', fillet, dist(i,i-1), do_not_fillet)
            obj_poly_track.fillets(fillet, do_not_fillet=do_not_fillet)
        return obj_poly_track, obj_poly_swp

    obj_polyline_center_tr, obj_polyline_center_trN = make_obj_polyline_track(name, cpw_center_w,
                                                                             combinekw(poly_default_options, {'transparency':0}))
    obj_polyline_center_gp, obj_polyline_center_gpN = make_obj_polyline_track(name+'_cut', cpw_center_gap)
    if options['do_mesh'] in TRUE_STR:
        obj_polyline_center_ms, obj_polyline_center_msN = make_obj_polyline_track('mesh_'+name, cpw_mesh_gap)

    ### MAKE SHEETS
    if not (options['do_only_lines'] in TRUE_STR):
        sheet_center_trace = oModeler._sweep_along_path(obj_polyline_center_trN, obj_polyline_center_tr)
        sheet_gap_trace    = oModeler._sweep_along_path(obj_polyline_center_gpN, obj_polyline_center_gp)
        if options['do_mesh'] in TRUE_STR:
            sheet_mesh_trace   = oModeler._sweep_along_path(obj_polyline_center_msN, obj_polyline_center_ms)

        # Subtract from ground plane   TODO: RENAME
        if options['do_subtract_ground'] in TRUE_STR:
            oModeler.subtract(design.get_ground_plane(options),
                              [sheet_gap_trace],
                              keep_originals = options['do_sub_keep_original'] in TRUE_STR)
        if options['do_assign_perfE']:
            #print(sheet_center_trace)
            oModeler.append_PerfE_assignment(str(sheet_center_trace) if options['BC_individual']\
                                                 else options['BC_name'], [str(sheet_center_trace)])
    else:
        sheet_center_trace, sheet_mesh_trace =None, None

    ### Handle design tracking - track as much information as possible
    if 0:
        design.add_track_object(options, {
                                    'options'    : options,
                                    'points'     : points,
                                    'mesh_obj_name'      : obj_polyline_center_msN,
                                    'center_tr_obj_name' : obj_polyline_center_trN,
                                    'sheet_center_trace' : sheet_center_trace,
                                    'sheet_mesh_trace'   : sheet_mesh_trace
                                   })
    ### Add connectors
    if options['do_add_connectors']:
        dist = cpw_center_w/2.*vec_n
        raise NotImplemented('Update make_connector -- add to design!?')
        design.connectors[name+'_start'] = make_connector([cpw_origin-dist, cpw_origin+dist], options)

        vec_D, vec_d, vec_n = vec_unit_norm([points[-2], points[-1]])
        dist, cpw_end = cpw_center_w/2.*vec_n, points[-1] # TODO: might need to play with orientation here
        raise NotImplemented('Update make_connector -- add to design!?')
        design.connectors[name+'_end'] = make_connector([cpw_end-dist, cpw_end+dist], options)

    if 1:
        design.mesh_obj(str(sheet_mesh_trace), options['mesh_name'], **options['mesh_kw'])

    #return  TODO: return objects here



def connector_cpw_plotme(points0, points,label=None, plot_control=False,
                        orient_HFSS=+1, ax=None):
    '''
    Quick and  dirty utility for plotting a list of points.
    Uses the default HFSS orientation

    Args:
        orient_HFSS (-1,+1): Rotate the plot to make into default hfss
        orientation or not.
    '''
    points0 = array(points0)
    if ax is None:
        ax = plt.gca()
    else:
        ax = ax
    #ax.grid(True)

    if orient_HFSS is -1:
        if plot_control:
            plt.plot(points0[:,1], orient_HFSS*points0[:,0], marker='o',ms=3,alpha=0.6, label=label)
        plt.plot(points[:,1], orient_HFSS*points[:,0], marker='o',ms=3,alpha=0.6)
        ax.set_ylabel('-X')
        ax.set_xlabel('Y')
    else:
        if plot_control:
            plt.plot(points0[:,0], points0[:,1], marker='o',ms=3,alpha=0.6, label=label)
        plt.plot(points[:,0], points[:,1], marker='o',ms=3,alpha=0.6)




##############################################################################
###
###  MEANDER
###

DEFAULT_OPTIONS['basic_meander'] = {
    'spacing'         : '0.2mm',  # between meanders
    'width'           : '-1mm',   # can be negative or positve
    'shift_fraction'  : 0,        # between -1 and +1
    'snap_toXY'       : True,
    'snap_force_ort'  : False,    # forceorhtogonal snap
    'lead_in_spacing' : '0.2mm',
    'direction_sign'  : +1,
    }
def basic_meander(design, points0,
                  options):
    '''
    Assumes:
        1. Points are 2D
        2. Points are in the default USER units, mm (i.e., not yet parsed).
           This funciton will work in the user unit space

    Can be use dot do things like this :

    .. figure:: figures/meander2.PNG
        :align: center
        :width: 5in

    '''

    assert len(points0) == 2
    options = combinekw(DEFAULT_OPTIONS['basic_meander'], options)
    meander_spacing, meander_out, shift_fraction, lead_in_spacing = \
        design.get_option_values(options,'spacing, width, shift_fraction, lead_in_spacing')

    # print('meander_spacing = {meander_spacing}')

    meander_out = meander_spacing/2. if meander_out is None else meander_out/2.0
    points0 = list(map(np.array, points0))          # enforce numpy array
    points  = remove_colinear_pts(np.array(points0))
    vec_D, vec_d, vec_n = vec_unit_norm(points0) # distance vector, unit dist. vector, normal unit vector

    if options['snap_toXY']:
        def snap_unit_vector_toXY(vec_n):
            ''' snaps to either the x or y unit vecotrs'''
            m = np.argmax(abs(vec_n))
            m = m if options['snap_force_ort'] == False else int(not(m))
            v = np.array([0,0])
            v[m] = np.sign(vec_n[m])
            vec_n = v
            return vec_n
        vec_n = snap_unit_vector_toXY(vec_n)
        vec_d = snap_unit_vector_toXY(vec_d)


    s1, s2 = 1-shift_fraction, 1+shift_fraction
    ds = options['direction_sign']
    Nmax    = int(np.floor( (norm(np.dot(vec_D,vec_d)) - lead_in_spacing) / (meander_spacing)))
    Steps   = [[+ds*meander_out*s1*vec_n, meander_spacing*vec_d, -ds*meander_out*s2*vec_n],
               [-ds*meander_out*s1*vec_n, meander_spacing*vec_d, +ds*meander_out*s2*vec_n]
              ]
    #Steps   = [[+meander_out*vec_n, meander_spacing*vec_d, -meander_out*vec_n],
    #           [-meander_out*vec_n, meander_spacing*vec_d, +meander_out*vec_n]
    #          ]

    points = [points0[0]]
    points+= [points0[0] + lead_in_spacing*vec_d]

    for n in range(Nmax):
        steps = Steps[np.mod(n, len(Steps))]
        for nn, step in enumerate(steps):
            last_point = points[-1]
            points += [last_point + step]

    final_pt = points0[1]
    if 1: # alter the last point  so it isnt at an angle
        # this willl fail when they overlap
        pts   = points[-2:]
        unitv = vec_unit_planar(pts)
        #dist  = norm(pts)
        line  = LineString([points[-1]+unitv*100,points[-1]-unitv*100]) # span enoguh space
        point = line.interpolate(line.project(Point(final_pt)))
        points[-1] = np.array(point.coords)[0]

    points += [final_pt]

    return remove_colinear_pts(points)

def meander_between(design, points, start_idx, meander_options):
    '''
    Specify to mender b/w two control points in an array
    Units should be USER units

    Handles coliner points - removes the colinear extra point
    This causes issues in HFSS.

    Wrapper function calls `basic_meander`
    '''
    meander = basic_meander(design, points[start_idx: start_idx+2], meander_options)
    points  = np.delete(points, [start_idx, start_idx+1], axis=0)
    points  = np.insert(points, start_idx, meander, axis=0)
    points  = remove_colinear_pts(points) # it is possible to get 3 colinear points
    return points



DEFAULT_OPTIONS['easy_connect'] = Dict(
    _calls = ['meander_between', 'connector_cpw_plotme', 'draw_cpw_trace', 'basic_meander']
)


DEFAULT_OPTIONS['easy_wirebond'] = Dict(
    w='0.2mm', # widhrt of wirebond
    height='0.15mm', # height of wirebond
    offset='0.2mm', # from center of line segment
    category='cpw', # depricated for now
    threshold='0.22mm', # min line sgement
    start=0,
    stop=-1,
    step=1,
)


def easy_wirebond(design, obj,
                  options = {},
                  name = None,
                  draw_hfss=True,
                  parent_obj = None):
    '''
    TODO: split into make and draw maybe add as funciton to cpw_ base object? that calls this

    Add wire bonds automatically to a CPW trace given a certain spacing

    Assumes zero elevation for chip. Not flip chip

    Units: User units



    OLD raw use:
        from qiskit_metal.draw.cpw import *
        name = 'cpw_Q1_bus_Q2_Q2_bus_Q1'
        easy_wirebond(design, objects[name], 'Bond_'+name, Dict(
            start=0, stop=-1, step=2, threshold='0.2mm'))

    TEST:
        options = objects['cpw_Q1_bus_Q2_Q2_bus_Q1']['options_hfss']
        cpw_line = objects['cpw_Q1_bus_Q2_Q2_bus_Q1']['objects']['cpw_line']#.components.cpw_line
        points_meander = np.array(cpw_line.coords)
    '''

    options = {**DEFAULT_OPTIONS['easy_wirebond'], **options} # overwritten for Metal Object

    ############################################
    # Get points of cpw and handle Metal Object
    from .components.base_objects.Metal_Utility import is_component

    if is_component(obj):

        if parent_obj is None:
            parent_obj = obj

        if name is None:
            name ='Bond_' + obj.name

        options = {**DEFAULT_OPTIONS['easy_wirebond'],
                   **obj.options.easy_wirebond, # if there are already wirebond options
                   **options}

        if 'cpw_line' in obj.components:
            points_meander = np.array(obj.components.cpw_line.coords)
        else:
            raise Exception('Object {obj} does not have obj.components.cpw_line')

    ############################################
    # Handle non metal obejcts (yes, too many here, not all needed)
    elif isinstance(obj, Dict):
        if ('objects' in obj):
            if 'cpw_line' in obj.components:
                points_meander = np.array(obj.components.cpw_line.coords)
            else:
                raise Exception('Unkown object {obj} does not have obj.components.cpw_line')
        else:
            raise Exception('Unkown object {obj}: does not have obj.components')
    elif isinstance(obj, str):
        points_meander = np.array(unparse_units(design.track_objs[options['category']][obj]['points']))
        #DEPRICATED here
    elif isinstance(obj, draw.LineString):
        points_meander = np.array(obj.coords)
    elif isinstance(obj, np.ndarray) or isinstance(obj, list):
        points_meander = np.array(obj)
    else:
        points_meander = np.array(obj)
        logger.error(
            'ERROR: UNKOWN INPUT OBJECT! Cannot convert to points!  Trying to procees')
        raise Exception('See logger error.')

    ############################################
    # Core part of procedure
    #
    # Figure out new control points and draw
    # Place once per segment;  iterate each path segement

    start, stop, step = [options[n.strip()] for n in ('start, stop, step'.split(','))]
    w, ofst, th, height  = design.parse_params('w,offset,threshold,height')

    wirebond_names = []
    shapes = {}
    for i in range(start, len(points_meander) + stop, step):
        p1, p2 = map(array, points_meander[i:i+2])
        vec_D, vec_d, vec_n = vec_unit_norm([p1, p2])
        #print(p1, vec_n, norm(vec_D), '\n ',p1,p2, vec_n ) #render_to_mpl([Point(p1),Point(p2)])

        if (norm(vec_D) > th) and (norm(vec_D)/2. >  ofst): # if the segment is longer than thresohld place a bond
           # make sure wirbondf doesn stick out
            pos, ori = [(p1+p2)/2., vec_n]
            pos -= ofst*vec_d   # w*vec_n/2.

            p = np.array(pos)
            shapes[str(i)] = dict(center=Point(pos),
                             bond = LineString([p-ori*w/2, p+ori*w/2]))
            #render_to_mpl(shapes[i]) # draw shapely
            if draw_hfss:
                _, oModeler = design.get_modeler() ###
                wirebond_names += [
                    oModeler.draw_wirebond(parse_units(pos), ori, parse_units(w),
                                        height=parse_units(height),
                                        name=name+f'_{i}',
                                        material='pec',
                                        solve_inside = False)]

    ############################################
    #
    # Save new objects to parent object
    if not (parent_obj is None):

        if is_component(obj):
            obj = parent_obj
            obj.components.wirebonds = shapes
            obj.hfss_objects = wirebond_names
            obj.options.easy_wirebond = options
        else:
            if not ('hfss_objects' in parent_obj):
                parent_obj['hfss_objects'] = Dict()

            parent_obj['hfss_objects']['wirebonds'] = Dict(
                options_easy_wirebond = options,
                wirebond_names = wirebond_names
            )
            parent_obj['objects_wirebond'] = shapes
