# Qiskit Metal 
[![License](https://img.shields.io/github/license/Qiskit/qiskit-metal.svg?style=popout-square)](https://opensource.org/licenses/Apache-2.0)<!--- long-description-skip-begin -->[![Release](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)<!--- long-description-skip-begin -->[![join slack](https://img.shields.io/badge/slack-@qiskit-yellow.svg?logo=slack&style=popout-square)](https://qisk.it/join-slack)[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4618153.svg)](https://doi.org/10.5281/zenodo.4618153)
 
>![Welcome to Qiskit Metal!](https://raw.githubusercontent.com/Qiskit/qiskit-metal/main/docs/images/zkm_banner.png 'Welcome to Qiskit Metal')
> Qiskit Metal is an open-source framework for engineers and scientists to design superconducting quantum devices with ease.


## Major Update: Upcoming Qiskit Metal Release 🚀
We're excited to share that we're nearing the completion of porting Qiskit Metal from PySide2 to PySide6! This update enables native support for M* Macs (Apple Silicon) and includes several other enhancements for the upcoming release. Please take a moment to review and provide feedback on [Pull Request #1002](https://github.com/qiskit-community/qiskit-metal/pull/1002) before we proceed with merging and tagging. Your input is invaluable to ensure the release meets everyone's expectations. Thank you for your continued contributions!

## Installation
If you are interested in customizing your experience, or if you are unable to install qiskit-metal using the `pip install` instructions below, consider installing directly the source code, following the instructions in the [documentation](https://qiskit-community.github.io/qiskit-metal/installation.html) and/or the [installation instructions for developers](https://github.com/Qiskit/qiskit-metal/blob/main/README_developers.md).

For normal use, please continue reading.

### The Qiskit Metal deployed package
You can install Qiskit Metal via the pip tool (a python package manager).
```bash
pip install qiskit-metal
```
PIP will handle most of the dependencies automatically and you will always install the latest (and well-tested) version of the package.

Some of the dependencies, namely pyside2 and geopandas, might require manual installation, depending on your specific system compatibility. If you encounter installation or execution errors, please refer first to the [FAQ](https://qiskit-community.github.io/qiskit-metal/faq.html).

We recommend to install qiskit-metal in a conda environment or venv, to prevent version conflicts with pre-existing package versions.

### Jupyter Notebook
At this time, we recommend using Jupyter notebook/lab to be able to access all the Qiskit Metal features. Jupyter is not installed with the default dependencies, to accommodate those users intending to utilize a centralized or customized installation.

If you require a fresh installation, please refer to either [anaconda.org](https://anaconda.org/) or [jupyter.org](https://jupyter.org/install).

Unless you installed the entire `jupyter` package in your current environment, do not forget to create the appropriate kernel to make the environment (thus qiskit-metal) available to jupyter (instructions in the [FAQ](https://qiskit-community.github.io/qiskit-metal/faq.html))

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
>>> q1.options.pad_height = '90um'
>>> q1.options.pad_width  = '455um'
>>> q1.options.pad_gap    = '30 um'
```
#### Update the component geometry after changing the options.
```python
>>> gui.rebuild()
```
![Example_Image!](https://raw.githubusercontent.com/Qiskit/qiskit-metal/main/docs/images/1_1_Birds_eye_view_of_Qiskit_Metal_example_image.jpg 'Example_Image') 
#### Get a list of all the qcomponents in QDesign and then zoom on them.
```python
>>> all_component_names = design.components.keys()
>>> gui.zoom_on_components(all_component_names)
```
#### Closing the Qiskit Metal GUI.
```python
>>> gui.main_window.close()
```

A script is available [here](https://qiskit-community.github.io/qiskit-metal/tut/overview/1.1%20High%20Level%20Demo%20of%20Qiskit%20Metal.html), where we also show the overview of Qiskit Metal.

## Community and Support

#### Watch the recorded tutorials 
[![Video Tutorials](https://img.shields.io/badge/youtube-Video_Tutorials-red.svg?logo=youtube)](https://youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb)

The streaming will also be recorded and made available [here](https://www.youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb) for offline review.

#### Take part in the live tutorials and discussion
Through June 2021 we are offering live tutorials and Q&A. [Sign up](https://airtable.com/shrxQEgKqZCf319F3) to receive an invite to the upcoming sessions.  The streaming will also be recorded and made available for offline review.  Find [here](https://github.com/Qiskit/qiskit-metal/blob/main/README_Tutorials.md) more details on schedule and use the Slack channel to give us feedback and to request the most relevant content to you.

#### Get help: Slack 
[![join slack](https://img.shields.io/badge/slack-blue.svg?logo=slack)](https://qisk.it/join-slack)

Use the slack channel.  Join [qiskit slack](https://qisk.it/join-slack) and then join the `#metal` channel to communicate with the developers and other participants.  You may also use this channel to inquire about collaborations.

## Contribution Guidelines
If you'd like to contribute to Qiskit Metal, please take a look at our
[contribution guidelines](https://github.com/Qiskit/qiskit-metal/blob/main/CONTRIBUTING.md). This project adheres to Qiskit's [code of conduct](https://github.com/Qiskit/qiskit-metal/blob/main/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
We use [GitHub issues](https://github.com/Qiskit/qiskit-metal/issues) for tracking requests and bugs. Please
[join the Qiskit Slack community](https://qisk.it/join-slack)
and use our [Qiskit Slack channel](https://qiskit.slack.com) for discussion and simple questions.
For questions that are more suited for a forum we use the Qiskit tag in the [Stack Exchange](https://quantumcomputing.stackexchange.com/questions/tagged/qiskit).
## Next Steps
Now you're set up and ready to check out some of the other examples from our
[Qiskit Metal Tutorials](https://github.com/Qiskit/qiskit-metal/blob/main/tutorials/) repository or [Qiskit Metal Documentation](https://qiskit-community.github.io/qiskit-metal/tut/).
## Authors and Citation
Qiskit Metal is the work of [many people](https://github.com/Qiskit/qiskit-metal/pulse/monthly) who contribute to the project at different levels. Metal was conceived and developed by [Zlatko Minev](https://www.zlatko-minev.com) at IBM; then co-led with Thomas McConkey. If you use Qiskit Metal, please cite as per the included [BibTeX file](https://github.com/Qiskit/qiskit-metal/blob/main/Qiskit_Metal.bib). For icon attributions, see [here](https://github.com/Qiskit/qiskit-metal/blob/main/qiskit_metal/_gui/_imgs/icon_attributions.txt).
## Changelog and Release Notes
The changelog provides a quick overview of notable changes for a given release.

The changelog for a particular release can be found in the correspondent Github release page. For example, you can find the changelog for the `0.0.4` release [here](https://github.com/Qiskit/qiskit-metal/releases/tag/0.0.4)

The changelog for all releases can be found in the release page: [![Releases](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)

Additionally, as part of each release detailed release notes are written to document in detail what has changed as part of a release. This includes any documentation on potential breaking changes on upgrade and new features.

## License
[Apache License 2.0](https://github.com/Qiskit/qiskit-metal/blob/main/LICENSE.txt)
