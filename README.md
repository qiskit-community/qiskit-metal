# Qiskit Metal 
[![License](https://img.shields.io/github/license/Qiskit/qiskit-metal.svg?style=popout-square)](https://opensource.org/licenses/Apache-2.0)<!--- long-description-skip-begin -->[![Release](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)<!--- long-description-skip-begin -->[![join slack](https://img.shields.io/badge/slack-@qiskit-yellow.svg?logo=slack&style=popout-square)](https://ibm.co/joinqiskitslack)[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4618153.svg)](https://doi.org/10.5281/zenodo.4618153)
 
>![Welcome to Qiskit Metal!](https://github.com/Qiskit/qiskit-metal/blob/main/docs/images/zkm_banner.png 'Welcome to Qiskit Metal')
> Qiskit Metal is an open-source framework for engineers and scientists to design superconducting quantum devices with ease.

## Installation
We encourage installing Qiskit Metal via the pip tool (a python package manager).
```bash
pip install qiskit-metal
```
PIP will handle all dependencies automatically and you will always install the latest (and well-tested) version. 

It is also recommended that you make a new conda environment before installing:

```bash
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install --no-deps -e .
```
#### Source Code Installation
To edit the code and truly customize the experience, if PyPI gives you trouble, or to install from source, follow the instructions in the [documentation](https://qiskit.org/documentation/metal/installation.html) and/or the [installation instructions for developers](/README_developers.md).

## Creating Your First Quantum Component in Qiskit Metal:
Now that Qiskit Metal is installed, it's time to begin working with it.
We are ready to try out a quantum chip example, which is simulated locally using
the Qiskit MetalGUI element. This is a simple example that makes a qubit.
```
$ python
```
```python
>>> from qiskit_metal import designs, draw, MetalGUI, Dict, open_docs
>>> design = designs.DesignPlanar()
>>> design.overwrite_enabled = True
>>> design.chips.main
>>> design.chips.main.size.size_x = '11mm'
>>> design.chips.main.size.size_y = '9mm'
>>> gui = MetalGUI(design)
```
#### Launch the Qiskit Metal GUI to interactively view, edit, and simulate a QDesign:
```python
>>> gui = MetalGUI(design)
```
#### Let's create a new qubit (a transmon) by creating an object of this class.
```python
>>> from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
>>> q1 = TransmonPocket(design, 'Q1', options=dict(connection_pads=dict(a=dict())))
>>> gui.rebuild()
>>> gui.edit_component('Q1')
>>> gui.autoscale()
```
#### Change options.
```python
>>> q1.options.pos_x = '0.5 mm'
>>> q1.options.pos_y = '0.25 mm'
>>> q1.options.pad_height = '225 um'
>>> q1.options.pad_width  = '250 um'
>>> q1.options.pad_gap    = '50 um'
```
#### Update the component geoemtry, since we changed the options.
```python
>>> gui.rebuild()
```
#### Get a list of all the qcomponents in QDesign and then zoom on them.
```python
>>> all_component_names = design.components.keys()
>>> gui.zoom_on_components(all_component_names)
```
#### Closing the Qiskit Metal GUI.
```python
>>> gui.main_window.close()
```

A script is available [here](https://qiskit.org/documentation/metal/tut/overview/1.1%20High%20Level%20Demo%20of%20Qiskit%20Metal.html), where we also show the overview of Qiskit Metal.

## Community and Support

#### Watch the recorded tutorials 
[![Video Tutorials](https://img.shields.io/badge/youtube-Video_Tutorials-red.svg?logo=youtube)](https://youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb)

The streaming will also be recorded and made available [here](https://www.youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb) for offline review.

#### Take part in the live tutorials and discussion
Through June 2021 we are offering live tutorials and Q&A. [Sign up](https://airtable.com/shrxQEgKqZCf319F3) to receive an invite to the upcoming sessions.  The streaming will also be recorded and made available for offline review.  Find [here](https://github.com/Qiskit/qiskit-metal/blob/main/README_Tutorials.md) more details on schedule and use the Slack channel to give us feedback and to request the most relevant content to you.

#### Get help: Slack 
[![join slack](https://img.shields.io/badge/slack-blue.svg?logo=slack)](https://ibm.co/joinqiskitslack)

Use the slack channel.  Join [qiskit slack](https://ibm.co/joinqiskitslack) and then join the `#metal` channel to communicate with the developers and other participants.  You may also use this channel to inquire about collaborations.

## Contribution Guidelines
If you'd like to contribute to Qiskit Metal, please take a look at our
[contribution guidelines](CONTRIBUTING.md). This project adheres to Qiskit's [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
We use [GitHub issues](https://github.com/Qiskit/qiskit-metal/issues) for tracking requests and bugs. Please
[join the Qiskit Slack community](https://ibm.co/joinqiskitslack)
and use our [Qiskit Slack channel](https://qiskit.slack.com) for discussion and simple questions.
For questions that are more suited for a forum we use the Qiskit tag in the [Stack Exchange](https://quantumcomputing.stackexchange.com/questions/tagged/qiskit).
## Next Steps
Now you're set up and ready to check out some of the other examples from our
[Qiskit Metal Tutorials](https://github.com/Qiskit/qiskit-metal/tutorials/) repository or [Qiskit Metal Documentation](https://qiskit.org/documentation/metal/tut/).
## Authors and Citation
Qiskit Metal is the work of [many people](https://github.com/Qiskit/qiskit-metal/pulse/monthly) who contribute to the project at different levels. Metal was conceived and developed by [Zlatko Minev](zlatko-minev.com) at IBM; then co-led with Thomas McConkey. If you use Qiskit Metal, please cite as per the included [BibTeX file](https://github.com/Qiskit/qiskit-metal/blob/main/Qiskit_Metal.bib). For icon attributions, see [here](/qiskit_metal/_gui/_imgs/icon_attributions.txt).
## Changelog and Release Notes
The changelog for a particular release is dynamically generated and gets
written to the release page on Github for each release. For example, you can
find the page for the `0.0.4` release here:
https://github.com/Qiskit/qiskit-metal/releases/tag/0.0.4
The changelog for the current release can be found in the releases tab:
[![Releases](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)
The changelog provides a quick overview of notable changes for a given
release.
Additionally, as part of each release detailed release notes are written to
document in detail what has changed as part of a release. This includes any
documentation on potential breaking changes on upgrade and new features.
## License
[Apache License 2.0](LICENSE.txt)
