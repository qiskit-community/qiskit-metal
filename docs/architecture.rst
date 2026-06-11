.. _architecture:

************
Architecture
************

Quantum Metal is organised around three load-bearing abstractions —
``QComponent`` (geometry pieces), ``QDesign`` (chip canvas), and
``QRenderer`` (export to GDS / HFSS / FEM). The viewers
(``MetalGUI`` and the new headless ``MetalGUIHeadless``) share the
same matplotlib renderer underneath; the ``qm.gui(design)`` factory
auto-picks one based on the environment.

.. mermaid::

   flowchart TB
       user["User code<br/><i>script, notebook, MetalGUI</i>"]

       subgraph design_layer["QDesign — designs/"]
           comps[design.components<br/><i>dict of QComponent</i>]
           qg[design.qgeometry<br/><i>shapely tables</i>]
           chips[design.chips<br/><i>chip stack</i>]
           vars[design.variables]
       end

       subgraph component_layer["QComponent — qlibrary/"]
           base[QComponent<br/><b>core/base.py</b>]
           qubits[qubits/]
           couplers[couplers/]
           tlines[tlines/]
           terms[terminations/]
           res[resonators/]
           base -.-> qubits & couplers & tlines & terms & res
       end

       subgraph renderer_layer["QRenderer — renderers/"]
           rbase[QRenderer / QRendererAnalysis<br/><b>renderer_base/</b>]
           mpl[renderer_mpl<br/><i>qm.view, MetalGUI canvas</i>]
           gds[renderer_gds<br/><i>GDS export</i>]
           ansys[renderer_ansys + renderer_ansys_pyaedt<br/><i>HFSS / Q3D</i>]
           fem[renderer_gmsh + renderer_elmer<br/><i>open FEM</i>]
           rbase -.-> mpl & gds & ansys & fem
       end

       subgraph analyses_layer["Analyses — analyses/"]
           ham[Hamiltonian quantization]
           cap[Capacitance / LOM]
           epr[Eigenmode + EPR]
       end

       subgraph gui_layer["Viewers — _gui/ + viewer/"]
           factory["qm.gui(design)<br/><i>auto-pick by env</i>"]
           metalgui[MetalGUI<br/><i>Qt desktop</i>]
           headless[MetalGUIHeadless<br/><i>inline matplotlib</i>]
           factory --> metalgui & headless
       end

       user --> design_layer
       user --> factory
       component_layer -- "construction registers" --> comps
       comps -- "make() / rebuild()" --> qg
       qg --> renderer_layer
       renderer_layer --> analyses_layer
       qg --> metalgui & headless

       classDef pri fill:#6929C4,stroke:#3D1773,color:#fff
       classDef sec fill:#e8defc,stroke:#6929C4,color:#1a1a1a
       classDef user_box fill:#fff4e3,stroke:#E07A5F,color:#1a1a1a
       class user user_box
       class base,rbase,factory pri
       class qubits,couplers,tlines,terms,res,mpl,gds,ansys,fem,metalgui,headless,ham,cap,epr,comps,qg,chips,vars sec

For deeper contributor-side detail on each abstraction (lifecycle,
options parsing, the lazy-Qt setup), read
``.claude/context/architecture.md`` in the repo root.
