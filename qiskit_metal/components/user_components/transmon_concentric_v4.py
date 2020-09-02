import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.components.base.qubit import BaseQubit

class TransmonConcentric(BaseQubit):

    # default drawing options 
    default_options = Dict(
        width='1000um',
        height='1000um',
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
        fbl_gap = '40um', # space between parallel lines of the flux bias loop
        fbl_ext = '300um', # run length of flux bias line between circular loop and edge of pocket 
        pocket_w = '1500um', # transmon pocket width 
        pocket_h = '1000um', # transmon pocket height 
        position_x = '5.0mm', 
        position_y = '5.0mm'
        )


    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers
        
        # draw the concentric pad regions 
        outer_pad = draw.Point(0,0).buffer(p.rad_o)
        space = draw.Point(0,0).buffer( (p.gap+p.rad_i) )
        outer_pad = draw.subtract(outer_pad, space)
        inner_pad = draw.Point(0,0).buffer(p.rad_i)
        
        # draw the top Josephson Junction (including translation)
        jj_port_top = draw.rectangle(p.jj_w, p.gap)
        jj_t = [jj_port_top]
        jj_t = draw.translate(jj_t, xoff=0.0,yoff=(p.rad_i+0.5*p.gap))

        # draw the bottom Josephson Junction (including translation)
        jj_port_bottom = draw.rectangle(p.jj_w, p.gap)
        jj_b = [jj_port_bottom]
        jj_b = draw.translate(jj_b, xoff=0.0, yoff=(-(p.rad_i+0.5*p.gap)))
        
        # draw the readout resonator  
        rr = draw.LineString([(-0.5*p.pocket_w, p.rad_o + p.res_s ),(p.res_ext,p.rad_o + p.res_s)])
        qp1 = (-0.5*p.pocket_w, p.rad_o + p.res_s ) # the first (x,y) coordinate is qpin #1 
        draw.mpl.render(rr, kw=dict(c='k'))
        
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
        draw.mpl.render(fbl, kw=dict(c='k'))
        
        # Translate all
        #objects = [outer_pad, inner_pad, jj_t, jj_b, pocket, rr, fbl]
        objects = [outer_pad, inner_pad, jj_t, jj_b, rr, fbl] # take pocket out ot make visualization easier 
        objects = draw.translate(objects, xoff=p.position_x, yoff=p.position_y)

        # EDIT HERE - Replace the following with your code
        # Create some raw geometry
        # Use autocompletion for the `draw.` module (use tab key)
        #rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        #rect = draw.rotate(rect, p.rotation)
        #geom = {'my_polygon': rect}
        #self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)
        

        # Draw all
        draw.mpl.clear_axis(ax)
        draw.mpl.render(objects)
        ax.autoscale()
        fig
        
    def make_connection_pad(self, name: str):
        # add pins
        points = np.array(connector_wire_path.coords)
        self.add_pin(pin1, points=qp1,
                     width=cpw_width, input_as_norm=True)
        self.add_pin(pin2, points=a,
                     width=cpw_width, input_as_norm=True)
        self.add_pin(pin3, points=i,
                     width=cpw_width, input_as_norm=True)
print("check")