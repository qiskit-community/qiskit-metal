.. _archive:

====================
Archived notebooks
====================

These notebooks stay at their URLs and keep their stored outputs. They are not
part of the learning path because another notebook covers the same ground.

.. list-table::
    :header-rows: 1
    :widths: 30 45 25

    * - Notebook
      - Reason
      - Use instead
    * - :doc:`Testing for overlap and collisions <tut/quick-topics/Testing-QComponents-for-overlap-and-collisions>`
      - Marked deprecated in its first cell in favor of ``qiskit_metal.validation``; no stored outputs.
      - :doc:`2.24 Design rule checking <tut/2-From-components-to-chip/2.24-Design-rule-checking>`
    * - :doc:`4.33 Transmon Analytics <tut/4-Analysis/4.33-Transmon-analytics>`
      - Plots the same eigenvalue figure as 4.32 with a fixed script (Ej/Ec = 1); no stored output.
      - :doc:`4.32 <tut/4-Analysis/4.32-Transmon-analytics-HCPB>`
    * - :doc:`A.5 Launch video example <circuit-examples/full-design-flow-examples/A.5-Launch-video-example>`
      - Written for a 2020 launch video; follows the same Ansys LOM/EPR pattern as A.7.
      - :doc:`A.7 <circuit-examples/full-design-flow-examples/A.7-IMS-2022-workshop>`, :doc:`A.4 <circuit-examples/full-design-flow-examples/A.4-Full-chip-design>`
    * - :doc:`A.6 Hackathon exercise, South Korea 2020 <circuit-examples/full-design-flow-examples/A.6-Hackathon-exercise-South-Korea-2020>`
      - Written for a 2020 event; follows the same pattern as A.7.
      - :doc:`A.7 <circuit-examples/full-design-flow-examples/A.7-IMS-2022-workshop>`
    * - :doc:`Four Qubit Chip Design <circuit-examples/F.Small-quantum-chips/51-Four_qubit_chip>`
      - Four-qubit chip without analysis; the same layout concept as A.3 and 2.21.
      - :doc:`A.3 <tut/full-design-examples/A.3-Four-qubit-multiplexed-readout>`, :doc:`2.21 <tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip>`
    * - :doc:`Single Transmon, floating, with charge lines <circuit-examples/A.Qubits/07-Transmon_floating_cl>`
      - Demonstrates the same class (``TransmonPocketCL``) as the Charge Line example.
      - :doc:`Charge Line <circuit-examples/E.Input-output-coupling/43-TransmonPocketCL>`
    * - :doc:`Opening the documentation <tut/quick-topics/Opening-documentation>`
      - One code cell; its content is in the FAQ.
      - :ref:`FAQ: opening and building the documentation <docs>`

.. toctree::
    :maxdepth: 1
    :hidden:

    tut/quick-topics/Testing-QComponents-for-overlap-and-collisions
    tut/4-Analysis/4.33-Transmon-analytics
    circuit-examples/full-design-flow-examples/A.5-Launch-video-example
    circuit-examples/full-design-flow-examples/A.6-Hackathon-exercise-South-Korea-2020
    circuit-examples/F.Small-quantum-chips/51-Four_qubit_chip
    circuit-examples/A.Qubits/07-Transmon_floating_cl
    tut/quick-topics/Opening-documentation
