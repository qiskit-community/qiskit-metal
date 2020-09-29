import numpy as np
from math import * 
from qiskit_metal import draw, Dict
from qiskit_metal.components.base.qubit import BaseQubit

class TransmonConcentric(BaseQubit):
    """
    The base 'TrasmonConcentric' class 
    
    Inherits 'BaseQubit' class
    
    Description:
        Metal transmon object consisting of a circle surrounding by a concentric 
        ring. There are two Josephson Junction connecting the circle to the ring; 
        one at the south end and one at the north end. There is a readout resonator. 
        
    Main Body:
        position_x / position_y = where the center of the transmon circle should be located on the chip. 
        width = width of the transmon pocket 
        height = height of the transmon pocket 
        rad_o = the outer radius defining the concentric ring 
        rad_i = the inner radius defining the concentric ring 
        gap = the distance between the transmon circle and the concentric ring 
        jj_w = the width of the Josephson Junction connecting the circle to the ring 
        res_s = the space between the top edge of the concentric ring and the readout resonator 
        res_ext = the distance which the readout resonator extends beyond the middle of the circle. 
        fbl_rad = the radius of the loop made by the flux bias line 
        fbl_sp = the separation between the concentric ring and the edge of the flux bias loop
        fbl_ext = the length of the straight portion of the flux bias loop 
        pocket_w = width of the transmon pocket containing all elements
        pocket_h = height of the transmon pocket containing all elements 
        rotation = degrees which the entire component is rotated by (counterclockwise)
        cpw_width = the width of the readout resonator and flux bias loop
        
    """ 

    # default drawing options
    default_options = Dict(
        width='1000um', # width of transmon pocket
        height='1000um', # height of transmon pocket
        layer='1',
        rad_o = '170um', # outer radius
        rad_i = '115um', # inner radius
        gap = '35um', # radius of gap between two pads
        jj_w = '10um', # Josephson Junction width
        res_s = '100um', # space between top electrode and readout resonator
        res_ext = '100um', # extension of readout resonator in x-direction beyond midpoint of transmon
        fbl_rad = '100um', # radius of the flux bias line loop
        fbl_sp = '100um',  # spacing between metal pad and flux bias loop
        fbl_gap = '80um', # space between parallel lines of the flux bias loop
        fbl_ext = '300um', # run length of flux bias line between circular loop and edge of pocket
        pocket_w = '1500um', # transmon pocket width
        pocket_h = '1000um', # transmon pocket height
        position_x = '2.0mm', # translate component to be centered on this x-coordinate
        position_y = '2.0mm', # translate component to be centered on this y-coordinate
        rotation = '0.0',   # degrees to rotate the component by
        cpw_width = '10.0um' # width of the readout resonator and flux bias line
        )
    """Default drawing options"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # draw the concentric pad regions
        outer_pad = draw.Point(0,0).buffer(p.rad_o)
        space = draw.Point(0,0).buffer( (p.gap+p.rad_i) )
        outer_pad = draw.subtract(outer_pad, space)
        inner_pad = draw.Point(0,0).buffer(p.rad_i)
        gap = draw.subtract(space, inner_pad)
        pads = draw.union(outer_pad, inner_pad)

        # draw the top Josephson Junction
        jj_port_top = draw.rectangle(p.jj_w, p.gap)
        jj_t = [jj_port_top]
        jj_t = draw.translate(jj_t, xoff=0.0,yoff=(p.rad_i+0.5*p.gap))

        # draw the bottom Josephson Junction
        jj_port_bottom = draw.rectangle(p.jj_w, p.gap)
        jj_b = [jj_port_bottom]
        jj_b = draw.translate(jj_b, xoff=0.0, yoff=(-(p.rad_i+0.5*p.gap)))

        # draw the readout resonator
        qp1a = (-0.5*p.pocket_w, p.rad_o + p.res_s ) # the first (x,y) coordinate is qpin #1
        qp1b = (p.res_ext,p.rad_o + p.res_s) # the second (x,y) coordinate is qpin #1
        rr = draw.LineString([qp1a,qp1b])

        # draw the flux bias line
        a = (0.5*p.pocket_w, -0.5*p.fbl_gap)
        b = (0.5*p.pocket_w - p.fbl_ext,-0.5*p.fbl_gap)
        c = (p.rad_o + p.fbl_sp + p.fbl_rad, -1.0*p.fbl_rad)
        d = (p.rad_o + p.fbl_sp + 0.2929*p.fbl_rad, 0.0 - 0.7071*p.fbl_rad)
        e = (p.rad_o + p.fbl_sp, 0.0)
        f = (p.rad_o + p.fbl_sp + 0.2929*p.fbl_rad, 0.0 + 0.7071*p.fbl_rad)
        g = (p.rad_o + p.fbl_sp + p.fbl_rad, p.fbl_rad)
        h = (0.5*p.pocket_w - p.fbl_ext,0.5*p.fbl_gap)
        i = (0.5*p.pocket_w, 0.5*p.fbl_gap)
        fbl = draw.LineString([a,b,c,d,e,f,g,h,i])

        # draw the transmon pocket bounding box
        pocket  = draw.rectangle(p.pocket_w, p.pocket_h)

        # Translate and rotate all shapes 
        objects = [outer_pad, inner_pad, jj_t, jj_b, pocket, rr, fbl]
        objects = draw.rotate(objects, p.rotation, origin=(0,0))
        objects = draw.translate(objects, xoff=p.position_x, yoff=p.position_y)
        [outer_pad, inner_pad, jj_t, jj_b, pocket, rr, fbl] = objects
  
        # define a function that both rotates and translates the qpin coordinates 
        def qpin_rotate_translate(x):
            y = list(x)
            z = [0.0, 0.0] 
            z[0] = y[0]*cos(p.rotation*3.14159/180) - y[1]*sin(p.rotation*3.14159/180)
            z[1] = y[0]*sin(p.rotation*3.14159/180) + y[1]*cos(p.rotation*3.14159/180)
            z[0] = z[0] + p.position_x
            z[1] = z[1] + p.position_y
            x = (z[0], z[1]) 
            return x 
        
        # rotate and translate the qpin coordinates        
        qp1a = qpin_rotate_translate(qp1a)
        qp1b = qpin_rotate_translate(qp1b)
        a = qpin_rotate_translate(a)
        b = qpin_rotate_translate(b)
        h = qpin_rotate_translate(h)
        i = qpin_rotate_translate(i) 

################################################################################################

        # Use the geometry to create Metal QGeometry
        geom_rr = {'path1': rr}
        geom_fbl = {'path2': fbl}
        geom_outer = {'poly1': outer_pad}
        geom_inner = {'poly2': inner_pad}
        geom_jjt = {'poly4': jj_t}
        geom_jjb = {'poly5': jj_b}
        geom_pocket = {'poly6': pocket}

        self.add_qgeometry('path', geom_rr, layer=1, subtract=False, width=p.cpw_width)
        self.add_qgeometry('path', geom_fbl, layer=1, subtract=False, width=p.cpw_width)
        self.add_qgeometry('poly', geom_outer, layer=1, subtract=False)
        self.add_qgeometry('poly', geom_inner, layer=1, subtract=False)
        self.add_qgeometry('poly', geom_jjt, layer=1, subtract=False)
        self.add_qgeometry('poly', geom_jjb, layer=1, subtract=False)
        self.add_qgeometry('poly', geom_pocket, layer=1, subtract=True)

##################################################################################################

        # Add Qpin connections
        self.add_pin('pin1',
                     points=np.array([qp1b,qp1a]),
                     width=0.01, input_as_norm=True)
        self.add_pin('pin2',
                     points=np.array([b,a]),
                     width=0.01, input_as_norm=True)
        self.add_pin('pin3',
                     points=np.array([h,i]),
                     width=0.01, input_as_norm=True)


