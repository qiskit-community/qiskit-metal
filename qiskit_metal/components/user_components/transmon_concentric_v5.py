import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.components.base.qubit import BaseQubit

class TransmonConcentric(BaseQubit):

    # default drawing options
    default_options = Dict(
        width='1000um', # width of transmon pocket 
        height='1000um', # height of transmon pocket 
        pos_x='0um',
        pos_y='0um',
        rotation='0',
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
        position_x = '5.0mm',
        position_y = '5.0mm',
        cpw_width = '10.0um'
        )


    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # draw the concentric pad regions
        outer_pad = draw.Point(0,0).buffer(p.rad_o)
        space = draw.Point(0,0).buffer( (p.gap+p.rad_i) )
        outer_pad = draw.subtract(outer_pad, space)
        inner_pad = draw.Point(0,0).buffer(p.rad_i)

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

        # Translate all
        objects = [outer_pad, inner_pad, jj_t, jj_b, pocket, rr, fbl]
        objects = draw.translate(objects, xoff=p.position_x, yoff=p.position_y)
#        [outer_pad, inner_pad, jj_t, jj_b, pocket, rr, fbl] = objects

################################################################################################

        # Use the geometry to create Metal QGeometry
        geom = {'path1': rr, 'path2': fbl}
        geom2 = {'poly1': outer_pad, 'poly2': inner_pad} #, 'poly3': jj_t, 'poly4': jj_b}
        geom3 = {'poly3': jj_t, 'poly4': jj_b} #, 'poly3': pocket}
        geom4 = {'poly5': pocket}
        self.add_qgeometry('path', geom, layer=1, subtract=False) #, width=p.cpw_width)
        self.add_qgeometry('poly', geom2, layer=1, subtract=False)
        self.add_qgeometry('poly', geom3, layer=1, subtract=False)
        self.add_qgeometry('poly', geom4, layer=1, subtract=True)

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

