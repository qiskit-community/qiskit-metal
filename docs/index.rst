####################################
Qiskit Metal |version| documentation
####################################

.. hint::

    You can open this documentation using

    .. code-block:: python

        import qiskit_metal
        qiskit_metal.open_docs()

.. attention::

    This is an alpha version of Qiskit Metal, the code is still under development.  Please let us know about anything you might want us to add or elaborate upon.


| **Qiskit for quantum hardware design (`Qiskit Metal`)** is a quantum device design and analysis SDK, library, and community.
| Call it quantum EDA (QEDA) and analysis.


.. rubric:: About Metal

Designing quantum devices is the bedrock of the quantum ecosystem, but it is a difficult, multi-step process that connects traditionally disparate worlds.

Metal is automating and streamlining this process. Our vision is to develop a community-driven universal platform capable of orchestrating quantum chip development from concept to fabrication in a simple and open framework.
Qiskit for quantum hardware design (`Qiskit Metal`) is:
* Open source
* Community-driven
* Both a python API and a front-end visual GUI interface.

Qiskit-metal is licensed under Apache 2.0. IBM reserves no copyright over outputs of qiskit-metal.

.. rubric:: Metal & it's vision (read full `Medium blog <https://medium.com/qiskit/what-if-we-had-a-computer-aided-design-program-for-quantum-computers-4cb88bd1ddea>`_):

.. highlights::

    We want to accelerate and lower the barrier to innovation on quantum devices.
    Today at the IEEE Quantum Week Conference, the team discussed their vision for this first-of-its-kind project. Led by quantum physicist Zlatko Minev and
    developed with other IBM Quantum team members, this project is meant for those interested in quantum hardware design: a suite of design automation
    tools that can be used to devise and analyze superconducting devices, with a focus on being able to integrate the best tools into a quantum hardware
    designer’s workflow. We’ve code-named the project Qiskit Metal.

    We hope that as a community, we might make the process of quantization — bridging the gap between pieces of a superconducting metal on a quantum chip
    with the computational mathematics of Hamiltonians and Hilbert spaces — available to anyone with a curious mind and a laptop. We want to make quantum
    device design a streamlined process that automates the laborious tasks as it does with conventional electronic device design. We are writing software
    with built-in best practices and cutting-edge quantum analysis techniques, all this while seamlessly leveraging the power of conventional EDA tools.
    The goal of Qiskit Metal is to allow for easy quantum hardware modeling with reduction of design-related errors plus increased speed.

**Qiskit Metal consists of four foundational elements:**

    - Quantum Device Design (QDesign): :ref:`qdesign`
    - Quantum Device Components (QComponent): :ref:`qlibrary`
    - Quantum Renderer (QRenderer): :ref:`qrenderer`
    - Quantum Analysis (QAnalysis): :ref:`qanalysis`

.. toctree::
    :maxdepth: 2
    :hidden:

    Metal Workflow<workflow>
    Frequently Asked Questions<faq>
    Code of Conduct<https://github.com/Qiskit/qiskit/blob/master/CODE_OF_CONDUCT.md>

.. TODO: Add Installing Qiskit Metal<getting_started/install.rst> before Metal Workflow
.. TODO: Add Getting Started With Metal between Metal Workflow and Installing Qiskit Metal

.. toctree::
    :maxdepth: 2
    :caption: Contributor Guide
    :hidden:

    Contributor Guide<contributor-guide>


.. toctree::
    :maxdepth: 2
    :caption: Tutorials
    :hidden:

    Overview<tut/tutorials/index.rst>

.. toctree::
    :maxdepth: 2
    :caption: Circuit Example Library
    :hidden:

    Qubits<circuit-examples/qubits/index>
    Resonators<circuit-examples/resonators/index>
    Composite Bi-Partite Systems Comprising Qubit and Resonator<circuit-examples/composite-bi-partite/index>
    Qubit Couplers<circuit-examples/qubit-couplers/index>
    Input-Output Coupling<circuit-examples/input-output-coupling/index>
    Small Quantum Chips<circuit-examples/small-quantum-chips/index>

.. toctree::
    :maxdepth: 2
    :caption: Libraries
    :hidden:

    Quantum Devices<apidocs/qlibrary>

.. toctree::
    :maxdepth: 2
    :caption: API References
    :hidden:

    Overview<overview>
    QDesigns<apidocs/designs>
    QComponents<apidocs/qlibrary>
    Analyses<apidocs/analyses>
    Renderer<apidocs/renderers>
    Toolbox<apidocs/toolbox_metal>

.. toctree::
    :maxdepth: 2
    :caption: Advanced API Reference
    :hidden:

    QGeometry<apidocs/qgeometries>
    GUI<apidocs/gui>


.. Hiding - Indices and tables
   :ref:`genindex`
   :ref:`modindex`
   :ref:`search`
