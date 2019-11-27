

# Not sure if this file will be used like this

# Mostly placeholder!

'''
:do_PerfE:       Applied p-erf E BC
:do_cut:         Cut from ground plane
:do_mesh:        Do mesh rect draw and specify mesh size
:BC_individual:  Apply individual names ot each BC, otherwise requires BC_name
:col_in_cond:    Default color for the inner conductors
.. math::

    n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k

'''

from ... import Dict
Dict(
    do_mesh=True,  # do mesh rect draw and specify mesh size
    do_PerfE=True,  # applied p-erf E BC
    do_cut=True,  # cut from ground plane
    BC_individual=False,  # Apply individual names ot each BC, otherwise requires BC_name
    # (196,202,206), # Default color for the inner conductors 100,120,90
    col_in_cond=(255, 0, 0),
    colors=Dict(
        ground_main=(100, 120, 140),  # lighter:  (196,202,206)
    )
)
