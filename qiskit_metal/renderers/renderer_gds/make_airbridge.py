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
""" For GDS export, separate the logic for airbridging."""

import gdspy
import shapely
import numpy as np

from qiskit_metal.qlibrary.core import QComponent
from airbridge import Airbridge


class Airbridging:

    def __init__(self,
                 design: 'QDesign',
                 lib: gdspy.GdsLibrary,
                 minx: float,
                 miny: float,
                 maxx: float,
                 maxy: float,
                 chip_name: str,
                 precision: float):
        # Design variables
        self.design = design
        self.lib = lib

        # Chip setup variables
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.chip_name = chip_name
        self.precision = precision


    @property
    def cpws_with_ab(self) -> 'DataFrame':
        '''
        QGeometry of CPWs w/ airbridges

        Returns:
            cpws_df (DataFrame): QGeometry of CPWs w/ airbridges
        '''
        path_qgeom = self.design.qgeometry.tables['path']
        cpws_df = path_qgeom[path_qgeom['gds_make_airbridge'] == True]
        return cpws_df

    #### TODO: still working on this ####
    def apply_uniform_airbridging(self, 
                                  custom_qcomponent: 'QComponent', 
                                  qcomponent_options: dict,
                                  bridge_pitch: float,
                                  ) -> gdspy.GdsLibrary:
        # Get shapley cutout of airbridges
        shapely_geom = self.extract_shapely_from_unrendered_qcomponent(custom_qcomponent=custom_qcomponent, 
                                                                       qcomponent_options=qcomponent_options)

        # Place the airbridges
        for cpw_qgeom in self.cpws_with_ab:
            cpw_name = cpw_qgeom['name']
            self.find_ab_placement(cpw_name=cpw_name,
                                   bridge_minimum_spacing=,
                                   bridge_pitch=,
                                   precision=self.precision)

        pass
        return self.lib


    def find_uniform_ab_placement(self, 
                                  cpw_name: str, 
                                  bridge_minimum_spacing: float,
                                  bridge_pitch: float,
                                  precision: int = 12) -> list[tuple[float, float, float]]:
        '''
        Determines where to place the wirebonds given a CPW. 
        
        Inputs:
            cpw_name (str): Name of cpw to find airbridge placements.
            bridge_minimum_spacing: (float) -- Minimum spacing from corners. Units in mm.
            bridge_pitch: (float, in units mm) -- Spacing between the centers of each bridge. Units in mm.
            precision: (int, optional) -- How precise did you define your CPWs?
                                This parameter is meant to take care of floating point errors.
                                References number of decimal points relative to millimeters.
        
        Returns:
            ab_placements (list[tuple]): Where the airbridges should be placed given `cpw_name`.
        
            Data structure is in the form of list of tuples
            [(x0, y0, theta0),
             (x1, y1, theta1),
             ...,
             (xn, yn, thetan))]
            
            Units: 
            - x, y, new_crossover_length are in mm
            - theta is in degrees
        '''
        target_cpw = self.design.components[cpw_name]

        points = target_cpw.get_points()
        ab_placements = []
        points_theta = []
        
        fillet = self.design.parse_value(target_cpw.options.fillet)
        
        ### Handles all the straight sections ###
        for i in range(len(points)-1):
            # Set up parameters for this calculation
            pos_i = points[i]
            pos_f = points[i + 1]
            
            x0 = round(pos_i[0],precision)
            y0 = round(pos_i[1],precision)
            xf = round(pos_f[0],precision)
            yf = round(pos_f[1],precision)
            
            dl = (xf - x0, yf - y0)
            dx = dl[0]
            dy = dl[1]
            
            
            theta = np.arctan2(dy,dx)
            mag_dl = np.sqrt(dx**2 + dy**2)
            lprime = mag_dl - 2 * self.BRS1 
            
            # Now implement logic to uphold the LL design rules
            ## Determine what BRS1 should be. It must be >= 0.005 (5um)
            
            if fillet > self.BRS1:
                lprime = mag_dl - 2 * fillet
            else:
                lprime = mag_dl - 2 * self.BRS1 
            n = 1 #refers to the number of bridges you've already placed
            #Asking should I place another? If true place another one.
            while (lprime) >= (n * bridge_pitch):
                n += 1
            
            mu_x = (xf + x0)/2
            mu_y = (yf + y0)/2
            
            x = np.array([i * bridge_pitch * np.cos(theta) for i in range(n)])
            y = np.array([i * bridge_pitch * np.sin(theta) for i in range(n)])

            x = (x - np.average(x)) + mu_x
            y = (y - np.average(y)) + mu_y
            
            for i in range(n):
                ab_placements.append((x[i],y[i], np.degrees(theta), None))
            
            #This is for the corner points
            points_theta.append(theta)
            
        ### This handles all the corner / turning sections ###
        # First check to see if any turns exists
        if (len(points) > 2):
            corner_points = points_theta[1:-1]
            for i in range(len(corner_points)+1):
                
                # First check to see if we should 
                # even make an airbridge at this corner
                pos_i = points[i]
                pos_f = points[i + 1]
                
                x0 = round(pos_i[0],precision)
                y0 = round(pos_i[1],precision)
                xf = round(pos_f[0],precision)
                yf = round(pos_f[1],precision)
                
                mag_dl = np.sqrt((xf-x0)**2 + (yf-y0)**2)
                
                if mag_dl < fillet or mag_dl < self.BRS1:
                    continue
                
                # Now that we only have real turns
                # let's find the center trace of to align the wirebonds
                theta_f = points_theta[i + 1]
                theta_i = points_theta[i]
                
                dx = np.cos(theta_i) - np.cos(theta_f)
                dy = np.sin(theta_i) - np.sin(theta_f)
                
                theta = np.arctan2(dy, dx)
                                
                distance_circle_box_x = fillet * (1-np.abs(np.cos(theta)))
                distance_circle_box_y = fillet * (1-np.abs(np.sin(theta)))
                
                theta_avg = (theta_f + theta_i)/2
                
                x = points[i + 1][0] - distance_circle_box_x * np.sign(np.cos(theta))
                y = points[i + 1][1] - distance_circle_box_y * np.sign(np.sin(theta))
                
                ab_placements.append((x, y, np.degrees(theta_avg)))
        
        return ab_placements
    
    def extract_shapely_from_unrendered_qcomponent(self, 
                                                   custom_qcomponent: 'QComponent',
                                                   qcomponent_options: dict):
        '''

        Args:
            custom_qcomponent (QComponent): Class of QComponent, not called / instantiated.
            qcomponent_options (dict): Geometrical options for cusotm_qcomponent. In structure of cusotm_qcomponent.default_options.
            shapely_geometries (list[shapley])
        '''
        # Chck you put in a QComponent
        if not issubclass(custom_qcomponent, QComponent):
            raise ValueError('`custom_qcomponent` must be a child of `QComponent`.')

        # Make a name which won't interfer w/ other components
        test_name = 'initial_name'
        all_component_names = self.design.component.keys()
        while test_name in all_component_names:
            test_name += '1'
        
        # Temporarily render in QComponent
        qcomponent_obj = custom_qcomponent(self.design, test_name, options=qcomponent_options)
        # Extract shapley data
        shapely_geometries = qcomponent_obj.qgeometry_table('poly')
        # Delete it
        qcomponent_obj.delete()

        return shapely_geometries

