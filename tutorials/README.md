# Tutorials have moved to `docs/`

The tutorial notebooks now live in one place, next to the documentation that
renders them:

- **[`docs/tut/`](../docs/tut/)**: the numbered tutorials (1 Overview, 2 From
  components to chip, 3 Renderers, 4 Analysis), Appendix B, and the Appendix A
  reference designs;
- **[`docs/circuit-examples/`](../docs/circuit-examples/)**: Appendix C (circuit
  examples) and the Appendix A full-design-flow examples;
- shared input files (junction GDS, layer stacks, helper modules):
  [`docs/tut/resources/`](../docs/tut/resources/).

Read them rendered, with outputs, at
<https://qiskit-community.github.io/qiskit-metal/tut/>, or open any notebook in
Colab or Binder from the badges at its top.

Until September 2026 every notebook was kept twice, here (names with spaces)
and under `docs/` (hyphenated names, which the docs site needs), with a script
and a CI check to keep the copies identical. The copies here were removed; the
table below maps each old path to its new one.

| Old path (`tutorials/…`) | New path |
|---|---|
| 1 Overview/1.1 Quick start.ipynb | [docs/tut/1-Overview/1.1-Quick-start.ipynb](../docs/tut/1-Overview/1.1-Quick-start.ipynb) |
| 1 Overview/1.2 Bird's eye view of Quantum Metal.ipynb | [docs/tut/1-Overview/1.2-Bird's-eye-view-of-Quantum-Metal.ipynb](../docs/tut/1-Overview/1.2-Bird%27s-eye-view-of-Quantum-Metal.ipynb) |
| 1 Overview/1.3 Build a 4-qubit chip.ipynb | [docs/tut/1-Overview/1.3-Build-a-4-qubit-chip.ipynb](../docs/tut/1-Overview/1.3-Build-a-4-qubit-chip.ipynb) |
| 1 Overview/1.4 Saving Your Chip Design.ipynb | [docs/tut/1-Overview/1.4-Saving-Your-Chip-Design.ipynb](../docs/tut/1-Overview/1.4-Saving-Your-Chip-Design.ipynb) |
| 1 Overview/1.5 Parametric design - iterate and compare.ipynb | [docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb](../docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb) |
| 2 From components to chip/A. Using QComponents/2.01 How to use a QComponent.ipynb | [docs/tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent.ipynb](../docs/tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent.ipynb) |
| 2 From components to chip/B. Routing between QComponents/2.11 Routing 101.ipynb | [docs/tut/2-From-components-to-chip/2.11-Routing-101.ipynb](../docs/tut/2-From-components-to-chip/2.11-Routing-101.ipynb) |
| 2 From components to chip/B. Routing between QComponents/2.12 Simple Meander.ipynb | [docs/tut/2-From-components-to-chip/2.12-Simple-Meander.ipynb](../docs/tut/2-From-components-to-chip/2.12-Simple-Meander.ipynb) |
| 2 From components to chip/B. Routing between QComponents/2.13 Hybrid Auto and AStar.ipynb | [docs/tut/2-From-components-to-chip/2.13-Hybrid-Auto-and-AStar.ipynb](../docs/tut/2-From-components-to-chip/2.13-Hybrid-Auto-and-AStar.ipynb) |
| 2 From components to chip/B. Routing between QComponents/2.14 Get them all with MixedRoute.ipynb | [docs/tut/2-From-components-to-chip/2.14-Get-them-all-with-MixedRoute.ipynb](../docs/tut/2-From-components-to-chip/2.14-Get-them-all-with-MixedRoute.ipynb) |
| 2 From components to chip/B. Routing between QComponents/2.15 Airbridges.ipynb | [docs/tut/2-From-components-to-chip/2.15-Airbridges.ipynb](../docs/tut/2-From-components-to-chip/2.15-Airbridges.ipynb) |
| 2 From components to chip/C. My first full quantum chip design/2.21 Design a 4 qubit full chip.ipynb | [docs/tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip.ipynb](../docs/tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip.ipynb) |
| 2 From components to chip/C. My first full quantum chip design/2.22 Design 100 qubits programmatically.ipynb | [docs/tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically.ipynb](../docs/tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically.ipynb) |
| 2 From components to chip/C. My first full quantum chip design/2.23 Modify chip options.ipynb | [docs/tut/2-From-components-to-chip/2.23-Modify-chip-options.ipynb](../docs/tut/2-From-components-to-chip/2.23-Modify-chip-options.ipynb) |
| 2 From components to chip/C. My first full quantum chip design/2.24 Design rule checking.ipynb | [docs/tut/2-From-components-to-chip/2.24-Design-rule-checking.ipynb](../docs/tut/2-From-components-to-chip/2.24-Design-rule-checking.ipynb) |
| 2 From components to chip/D. How do I make my custom QComponent/2.31 Create a QComponent - Basic.ipynb | [docs/tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic.ipynb](../docs/tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic.ipynb) |
| 2 From components to chip/D. How do I make my custom QComponent/2.32 Create a QComponent - Advanced.ipynb | [docs/tut/2-From-components-to-chip/2.32-Create-a-QComponent-Advanced.ipynb](../docs/tut/2-From-components-to-chip/2.32-Create-a-QComponent-Advanced.ipynb) |
| 2 From components to chip/D. How do I make my custom QComponent/2.33 Add my QComponent to a reusable python file.ipynb | [docs/tut/2-From-components-to-chip/2.33-Add-my-QComponent-to-a-reusable-python-file.ipynb](../docs/tut/2-From-components-to-chip/2.33-Add-my-QComponent-to-a-reusable-python-file.ipynb) |
| 3 Renderers/3.1 Introduction to QRenderers.ipynb | [docs/tut/3-Renderers/3.1-Introduction-to-QRenderers.ipynb](../docs/tut/3-Renderers/3.1-Introduction-to-QRenderers.ipynb) |
| 3 Renderers/3.2 Export your design to GDS.ipynb | [docs/tut/3-Renderers/3.2-Export-your-design-to-GDS.ipynb](../docs/tut/3-Renderers/3.2-Export-your-design-to-GDS.ipynb) |
| 3 Renderers/3.3 Render your design to Ansys.ipynb | [docs/tut/3-Renderers/3.3-Render-your-design-to-Ansys.ipynb](../docs/tut/3-Renderers/3.3-Render-your-design-to-Ansys.ipynb) |
| 3 Renderers/3.4 How do I make my custom QRenderer.ipynb | [docs/tut/3-Renderers/3.4-How-do-I-make-my-custom-QRenderer.ipynb](../docs/tut/3-Renderers/3.4-How-do-I-make-my-custom-QRenderer.ipynb) |
| 3 Renderers/3.5 Render your design to Gmsh.ipynb | [docs/tut/3-Renderers/3.5-Render-your-design-to-Gmsh.ipynb](../docs/tut/3-Renderers/3.5-Render-your-design-to-Gmsh.ipynb) |
| 4 Analysis/A. Core - EM and quantization/4.01 Capacitance and LOM.ipynb | [docs/tut/4-Analysis/4.01-Capacitance-and-LOM.ipynb](../docs/tut/4-Analysis/4.01-Capacitance-and-LOM.ipynb) |
| 4 Analysis/A. Core - EM and quantization/4.02 Eigenmode and EPR.ipynb | [docs/tut/4-Analysis/4.02-Eigenmode-and-EPR.ipynb](../docs/tut/4-Analysis/4.02-Eigenmode-and-EPR.ipynb) |
| 4 Analysis/A. Core - EM and quantization/4.03 Impedance.ipynb | [docs/tut/4-Analysis/4.03-Impedance.ipynb](../docs/tut/4-Analysis/4.03-Impedance.ipynb) |
| 4 Analysis/A. Core - EM and quantization/4.04 New LOM and Fluxonium Example.ipynb | [docs/tut/4-Analysis/4.04-New-LOM-and-Fluxonium-Example.ipynb](../docs/tut/4-Analysis/4.04-New-LOM-and-Fluxonium-Example.ipynb) |
| 4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example with sequence.ipynb | [docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example-with-sequence.ipynb](../docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example-with-sequence.ipynb) |
| 4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example.ipynb | [docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example.ipynb](../docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.11 Analyze and tune a transmon.ipynb | [docs/tut/4-Analysis/4.11-Analyze-and-tune-a-transmon.ipynb](../docs/tut/4-Analysis/4.11-Analyze-and-tune-a-transmon.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.12 Analyze a resonator.ipynb | [docs/tut/4-Analysis/4.12-Analyze-a-resonator.ipynb](../docs/tut/4-Analysis/4.12-Analyze-a-resonator.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.13 Analyze transmon and resonator.ipynb | [docs/tut/4-Analysis/4.13-Analyze-transmon-and-resonator.ipynb](../docs/tut/4-Analysis/4.13-Analyze-transmon-and-resonator.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.14 Analyze a double hanger resonator (S Param).ipynb | [docs/tut/4-Analysis/4.14-Analyze-a-double-hanger-resonator.ipynb](../docs/tut/4-Analysis/4.14-Analyze-a-double-hanger-resonator.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.15 CPW kappa calculation.ipynb | [docs/tut/4-Analysis/4.15-CPW-kappa-calculation.ipynb](../docs/tut/4-Analysis/4.15-CPW-kappa-calculation.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.16 Analyze S21 of Hange Geometry with WirebondLunchpadDriven.ipynb | [docs/tut/4-Analysis/4.16-Analyze-S21-of-Hange-Geometry-with-WirebondLunchpadDriven.ipynb](../docs/tut/4-Analysis/4.16-Analyze-S21-of-Hange-Geometry-with-WirebondLunchpadDriven.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.17 Fit S21 of Hanger Resonator Geometry.ipynb | [docs/tut/4-Analysis/4.17-Fit-S21-of-Hanger-Resonator-Geometry.ipynb](../docs/tut/4-Analysis/4.17-Fit-S21-of-Hanger-Resonator-Geometry.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.18 Analyse a Resonator with Ports.ipynb | [docs/tut/4-Analysis/4.18-Analyse-a-Resonator-with-Ports.ipynb](../docs/tut/4-Analysis/4.18-Analyse-a-Resonator-with-Ports.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.19 Analyze a transmon using ElmerFEM.ipynb | [docs/tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM.ipynb](../docs/tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.19 Multiplanar with pyaedt for Ansys/DrivenModal_pyaedt_multiplanar.ipynb | [docs/tut/4-Analysis/pyaedt-multiplanar/DrivenModal-pyaedt-multiplanar.ipynb](../docs/tut/4-Analysis/pyaedt-multiplanar/DrivenModal-pyaedt-multiplanar.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.19 Multiplanar with pyaedt for Ansys/Eigenmode_pyaedt_multiplanar.ipynb | [docs/tut/4-Analysis/pyaedt-multiplanar/Eigenmode-pyaedt-multiplanar.ipynb](../docs/tut/4-Analysis/pyaedt-multiplanar/Eigenmode-pyaedt-multiplanar.ipynb) |
| 4 Analysis/B. Advanced - Direct use of the renderers/4.19 Multiplanar with pyaedt for Ansys/Q3D_pyaedt_multiplanar.ipynb | [docs/tut/4-Analysis/pyaedt-multiplanar/Q3D-pyaedt-multiplanar.ipynb](../docs/tut/4-Analysis/pyaedt-multiplanar/Q3D-pyaedt-multiplanar.ipynb) |
| 4 Analysis/C. Parametric sweeps/4.21 Capacitance matrix.ipynb | [docs/tut/4-Analysis/4.21-Capacitance-matrix.ipynb](../docs/tut/4-Analysis/4.21-Capacitance-matrix.ipynb) |
| 4 Analysis/C. Parametric sweeps/4.22 Eigenmode matrix.ipynb | [docs/tut/4-Analysis/4.22-Eigenmode-matrix.ipynb](../docs/tut/4-Analysis/4.22-Eigenmode-matrix.ipynb) |
| 4 Analysis/C. Parametric sweeps/4.23 Impedance and scattering Z S Y matrices.ipynb | [docs/tut/4-Analysis/4.23-Impedance-and-scattering-Z-S-Y-matrices.ipynb](../docs/tut/4-Analysis/4.23-Impedance-and-scattering-Z-S-Y-matrices.ipynb) |
| 4 Analysis/D. Hamiltonian models - after quantization/4.31 Plot quantum oscillator wavefunction.ipynb | [docs/tut/4-Analysis/4.31-Plot-quantum-oscillator-wavefunction.ipynb](../docs/tut/4-Analysis/4.31-Plot-quantum-oscillator-wavefunction.ipynb) |
| 4 Analysis/D. Hamiltonian models - after quantization/4.32 Transmon analytics HCPB.ipynb | [docs/tut/4-Analysis/4.32-Transmon-analytics-HCPB.ipynb](../docs/tut/4-Analysis/4.32-Transmon-analytics-HCPB.ipynb) |
| 4 Analysis/D. Hamiltonian models - after quantization/4.33 Transmon analytics.ipynb | [docs/tut/4-Analysis/4.33-Transmon-analytics.ipynb](../docs/tut/4-Analysis/4.33-Transmon-analytics.ipynb) |
| 4 Analysis/D. Hamiltonian models - after quantization/4.34 Transmon qubit CPB hamiltonian charge basis.ipynb | [docs/tut/4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis.ipynb](../docs/tut/4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis.ipynb) |
| 4 Analysis/D. Hamiltonian models - after quantization/cQED with the Jaynes-Cummings Interaction Model.ipynb | [docs/tut/4-Analysis/cQED-with-the-Jaynes-Cummings-Interaction-Model.ipynb](../docs/tut/4-Analysis/cQED-with-the-Jaynes-Cummings-Interaction-Model.ipynb) |
| 4 Analysis/D. Hamiltonian models - after quantization/Design and Simulation of a Cross-Resonance Gate.ipynb | [docs/tut/4-Analysis/Design-and-Simulation-of-a-Cross-Resonance-Gate.ipynb](../docs/tut/4-Analysis/Design-and-Simulation-of-a-Cross-Resonance-Gate.ipynb) |
| Appendix A Full design flow examples/A.1 Transmon with readout resonator.ipynb | [docs/tut/full-design-examples/A.1-Transmon-with-readout-resonator.ipynb](../docs/tut/full-design-examples/A.1-Transmon-with-readout-resonator.ipynb) |
| Appendix A Full design flow examples/A.2 Two coupled transmons.ipynb | [docs/tut/full-design-examples/A.2-Two-coupled-transmons.ipynb](../docs/tut/full-design-examples/A.2-Two-coupled-transmons.ipynb) |
| Appendix A Full design flow examples/A.3 Four-qubit multiplexed readout.ipynb | [docs/tut/full-design-examples/A.3-Four-qubit-multiplexed-readout.ipynb](../docs/tut/full-design-examples/A.3-Four-qubit-multiplexed-readout.ipynb) |
| Appendix A Full design flow examples/A.4 Full chip design.ipynb | [docs/circuit-examples/full-design-flow-examples/A.4-Full-chip-design.ipynb](../docs/circuit-examples/full-design-flow-examples/A.4-Full-chip-design.ipynb) |
| Appendix A Full design flow examples/A.5 Launch video example.ipynb | [docs/circuit-examples/full-design-flow-examples/A.5-Launch-video-example.ipynb](../docs/circuit-examples/full-design-flow-examples/A.5-Launch-video-example.ipynb) |
| Appendix A Full design flow examples/A.6 Hackathon exercise - South Korea 2020.ipynb | [docs/circuit-examples/full-design-flow-examples/A.6-Hackathon-exercise-South-Korea-2020.ipynb](../docs/circuit-examples/full-design-flow-examples/A.6-Hackathon-exercise-South-Korea-2020.ipynb) |
| Appendix A Full design flow examples/A.7 IMS 2022 workshop.ipynb | [docs/circuit-examples/full-design-flow-examples/A.7-IMS-2022-workshop.ipynb](../docs/circuit-examples/full-design-flow-examples/A.7-IMS-2022-workshop.ipynb) |
| Appendix B Quick topics/JJ Demo Notebook.ipynb | [docs/tut/quick-topics/JJ-Demo-Notebook.ipynb](../docs/tut/quick-topics/JJ-Demo-Notebook.ipynb) |
| Appendix B Quick topics/Managing pins.ipynb | [docs/tut/quick-topics/Managing-pins.ipynb](../docs/tut/quick-topics/Managing-pins.ipynb) |
| Appendix B Quick topics/Managing variables.ipynb | [docs/tut/quick-topics/Managing-variables.ipynb](../docs/tut/quick-topics/Managing-variables.ipynb) |
| Appendix B Quick topics/Opening documentation.ipynb | [docs/tut/quick-topics/Opening-documentation.ipynb](../docs/tut/quick-topics/Opening-documentation.ipynb) |
| Appendix B Quick topics/QComponent - 3-fingers capacitor.ipynb | [docs/tut/quick-topics/QComponent-3-fingers-capacitor.ipynb](../docs/tut/quick-topics/QComponent-3-fingers-capacitor.ipynb) |
| Appendix B Quick topics/QComponent - Interdigitated transmon.ipynb | [docs/tut/quick-topics/QComponent-Interdigitated-transmon.ipynb](../docs/tut/quick-topics/QComponent-Interdigitated-transmon.ipynb) |
| Appendix B Quick topics/Testing QComponents for overlap and collisions.ipynb | [docs/tut/quick-topics/Testing-QComponents-for-overlap-and-collisions.ipynb](../docs/tut/quick-topics/Testing-QComponents-for-overlap-and-collisions.ipynb) |
| Appendix C Circuit examples/A. Qubits/01-Transmon_cross.ipynb | [docs/circuit-examples/A.Qubits/01-Transmon_cross.ipynb](../docs/circuit-examples/A.Qubits/01-Transmon_cross.ipynb) |
| Appendix C Circuit examples/A. Qubits/02-Transmon_floating.ipynb | [docs/circuit-examples/A.Qubits/02-Transmon_floating.ipynb](../docs/circuit-examples/A.Qubits/02-Transmon_floating.ipynb) |
| Appendix C Circuit examples/A. Qubits/03-concentric_transmon.ipynb | [docs/circuit-examples/A.Qubits/03-concentric_transmon.ipynb](../docs/circuit-examples/A.Qubits/03-concentric_transmon.ipynb) |
| Appendix C Circuit examples/A. Qubits/04-Interdigitated_Transmon.ipynb | [docs/circuit-examples/A.Qubits/04-Interdigitated_Transmon.ipynb](../docs/circuit-examples/A.Qubits/04-Interdigitated_Transmon.ipynb) |
| Appendix C Circuit examples/A. Qubits/05-Transmon_cross_fl.ipynb | [docs/circuit-examples/A.Qubits/05-Transmon_cross_fl.ipynb](../docs/circuit-examples/A.Qubits/05-Transmon_cross_fl.ipynb) |
| Appendix C Circuit examples/A. Qubits/06-Transmon_floating_6.ipynb | [docs/circuit-examples/A.Qubits/06-Transmon_floating_6.ipynb](../docs/circuit-examples/A.Qubits/06-Transmon_floating_6.ipynb) |
| Appendix C Circuit examples/A. Qubits/07-Transmon_floating_cl.ipynb | [docs/circuit-examples/A.Qubits/07-Transmon_floating_cl.ipynb](../docs/circuit-examples/A.Qubits/07-Transmon_floating_cl.ipynb) |
| Appendix C Circuit examples/A. Qubits/08-JJ-Dolan.ipynb | [docs/circuit-examples/A.Qubits/08-JJ-Dolan.ipynb](../docs/circuit-examples/A.Qubits/08-JJ-Dolan.ipynb) |
| Appendix C Circuit examples/A. Qubits/09-JJ-Manhattan.ipynb | [docs/circuit-examples/A.Qubits/09-JJ-Manhattan.ipynb](../docs/circuit-examples/A.Qubits/09-JJ-Manhattan.ipynb) |
| Appendix C Circuit examples/A. Qubits/10-Transmon_floating_teeth.ipynb | [docs/circuit-examples/A.Qubits/10-Transmon_floating_teeth.ipynb](../docs/circuit-examples/A.Qubits/10-Transmon_floating_teeth.ipynb) |
| Appendix C Circuit examples/A. Qubits/11-Star_shaped_qubit.ipynb | [docs/circuit-examples/A.Qubits/11-Star_shaped_qubit.ipynb](../docs/circuit-examples/A.Qubits/11-Star_shaped_qubit.ipynb) |
| Appendix C Circuit examples/B. Resonators/11-Resonator_Meander.ipynb | [docs/circuit-examples/B.Resonators/11-Resonator_Meander.ipynb](../docs/circuit-examples/B.Resonators/11-Resonator_Meander.ipynb) |
| Appendix C Circuit examples/C. Composite-bi-partite/21-OneTransmonsWithMeanderAndOTG.ipynb | [docs/circuit-examples/C.Composite-bi-partite/21-OneTransmonsWithMeanderAndOTG.ipynb](../docs/circuit-examples/C.Composite-bi-partite/21-OneTransmonsWithMeanderAndOTG.ipynb) |
| Appendix C Circuit examples/D. Qubit-couplers/31-TwoCrossmonsTunableCoupler.ipynb | [docs/circuit-examples/D.Qubit-couplers/31-TwoCrossmonsTunableCoupler.ipynb](../docs/circuit-examples/D.Qubit-couplers/31-TwoCrossmonsTunableCoupler.ipynb) |
| Appendix C Circuit examples/D. Qubit-couplers/32-TwoTransmonsDirectCoupling.ipynb | [docs/circuit-examples/D.Qubit-couplers/32-TwoTransmonsDirectCoupling.ipynb](../docs/circuit-examples/D.Qubit-couplers/32-TwoTransmonsDirectCoupling.ipynb) |
| Appendix C Circuit examples/D. Qubit-couplers/33-TwoTransmonsWithMeander.ipynb | [docs/circuit-examples/D.Qubit-couplers/33-TwoTransmonsWithMeander.ipynb](../docs/circuit-examples/D.Qubit-couplers/33-TwoTransmonsWithMeander.ipynb) |
| Appendix C Circuit examples/E. Input-output-coupling/41-LaunchPad.ipynb | [docs/circuit-examples/E.Input-output-coupling/41-LaunchPad.ipynb](../docs/circuit-examples/E.Input-output-coupling/41-LaunchPad.ipynb) |
| Appendix C Circuit examples/E. Input-output-coupling/42-ResonatorAndLaunchPad.ipynb | [docs/circuit-examples/E.Input-output-coupling/42-ResonatorAndLaunchPad.ipynb](../docs/circuit-examples/E.Input-output-coupling/42-ResonatorAndLaunchPad.ipynb) |
| Appendix C Circuit examples/E. Input-output-coupling/43-TransmonPocketCL.ipynb | [docs/circuit-examples/E.Input-output-coupling/43-TransmonPocketCL.ipynb](../docs/circuit-examples/E.Input-output-coupling/43-TransmonPocketCL.ipynb) |
| Appendix C Circuit examples/F. Small-quantum-chips/51-Four_qubit_chip.ipynb | [docs/circuit-examples/F.Small-quantum-chips/51-Four_qubit_chip.ipynb](../docs/circuit-examples/F.Small-quantum-chips/51-Four_qubit_chip.ipynb) |
| Appendix C Circuit examples/F. Small-quantum-chips/52-Barends_5Qubit_Xmon_Processor.ipynb | [docs/circuit-examples/F.Small-quantum-chips/52-Barends_5Qubit_Xmon_Processor.ipynb](../docs/circuit-examples/F.Small-quantum-chips/52-Barends_5Qubit_Xmon_Processor.ipynb) |
| Appendix C Circuit examples/F. Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode.ipynb | [docs/circuit-examples/F.Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode.ipynb](../docs/circuit-examples/F.Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode.ipynb) |
| Appendix C Circuit examples/F. Small-quantum-chips/54-Wallraff_TwoQubit_Cell_Mesh.ipynb | [docs/circuit-examples/F.Small-quantum-chips/54-Wallraff_TwoQubit_Cell_Mesh.ipynb](../docs/circuit-examples/F.Small-quantum-chips/54-Wallraff_TwoQubit_Cell_Mesh.ipynb) |
| Appendix C Circuit examples/F. Small-quantum-chips/Full Physical Design of iSWAP Gates.ipynb | [docs/circuit-examples/F.Small-quantum-chips/Full-Physical-Design-of-iSWAP-Gates.ipynb](../docs/circuit-examples/F.Small-quantum-chips/Full-Physical-Design-of-iSWAP-Gates.ipynb) |
| FlipChip_designtutorial.ipynb | [docs/tut/2-From-components-to-chip/FlipChip-design-tutorial.ipynb](../docs/tut/2-From-components-to-chip/FlipChip-design-tutorial.ipynb) |
