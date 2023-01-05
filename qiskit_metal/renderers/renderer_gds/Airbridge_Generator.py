from qiskit_metal import Dict
from Airbridge import Airbridge
from decimal import Decimal
import numpy as np

class Airbridge_Generator():
    '''
    The Airbrdige_Generator class generates a set of airbridges given a CPW.
    
    NOTE TO USER: These QComponents should not be rendered into Ansys for simulation.
    These are to be exported to GDS for fabrication.
    
    Input:
    * design: (qiskit_metal.design)
    * target_cpw: (list of QComponent or single QComponent) -- which CPW do you want to generate airbridges on?
    * crossover_length: (float, in units mm) -- The length of the bridge
    
    Parameters associated w/ MIT LL Design Guidelines V1
    * BRS1: (float, in units mm)
    * BRS2: (float, in units mm)

    '''
    
    def __init__(self, design, target_cpws, crossover_length, BRS1, BRS2=0.070):
        '''
        Places all airbridges for a specific CPW given a minimum BRS1 and BRS2
        '''
        self.design = design
        self.target_cpws = target_cpws
        self.crossover_length = crossover_length # in units of mm
        self.BRS1 = BRS1 # in units of mm
        self.BRS2 = BRS2 # in units of mm
        
        
        # Places the airbridges
        counter = 0
        self.airbridges = []

        for target_cpw in self.target_cpws:
            coordinates = self.find_ab_placement(target_cpw)
            for coord in coordinates:
                try:
                    name = "AB_{}".format(counter)
                    airbridge_qcomponent = self.make_single_ab(coord, name)
                    self.airbridges.append(airbridge_qcomponent)
                    counter += 1
                except:
                    pass
    
    def make_single_ab(self,coord,name):
        '''
        Tells Qiskit to add a single airbridge into your design

        Input:
        * coord (tuple) -- formatted (x,y,orientation,modulated crossover_length)
        * name (string) -- Name this airbridge.
                           Note: if you're making multiple, you'll want to increment the name

        '''
        x = coord[0]
        y = coord[1]
        orientation = coord[2] + 90
        options = Dict(pos_x = x,
                       pos_y = y,
                       orientation = orientation,
                       crossover_length = self.crossover_length)
        if coord[3] != None:
            options.crossover_length = coord[3]

        return Airbridge(self.design, name, options=options)
        
    
    def find_ab_placement(self, target_cpw, precision=12):
        '''
        Determins where to place the wirebonds given your set up
        
        Inputs:
        * precision: (int) -- How precise did you define your CPWs?
                              This parameter is meant to take care of
                              floating point errors.
        
        Outputs:
        Where the airbridges should be placed given set up
        
        Data structure is in the form of list of tuples
        [(x0, y0, theta0, new_crossover_length0),
         (x1, y1, theta1, new_crossover_length1),
         ...,
         (x_n, y_n, theta_n)]
        
        Units: 
        - x, y, new_crossover_length are in mm
        - theta is in degrees
        '''
        
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
            while (lprime) >= (n * self.BRS2):
                n += 1
            
            mu_x = (xf + x0)/2
            mu_y = (yf + y0)/2
            
            x = np.array([i * self.BRS2 * np.cos(theta) for i in range(n)])
            y = np.array([i * self.BRS2 * np.sin(theta) for i in range(n)])

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
                
                ab_placements.append((x, y, np.degrees(theta_avg), None))
        
        return ab_placements 
