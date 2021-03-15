# Docs for Qiskit Metal
There is no need to build the docs unless you want to.  In lieu of building the docs you can find them at https://qiskit.org/documentation/metal/.

If you choose to build the docs yourself, there are two methods described below to do that.

## The automated method
This folder contains the doc file src. We use sphinx to build the docs. _Docs may take up to 15 minutes to build._

Build the docs by executing this line:
```
    $ python docs/build_docs.py
```
Congratulations!  The docs can now be found in your `docs\build\html` directory.
## The step by step method
### Setup your environment to build the docs
1. Install sphinx and numpydoc
```
	 conda install sphinx numpydoc
	 (or pip install -U Sphinx)
```
2. Install read [the docs theme](https://github.com/Qiskit/qiskit_sphinx_theme) and set in the config `html_theme = “qiskit_sphinx_theme”`
```
	pip install qiskit_sphinx_theme
```
3. Install required packages
```
	pip install sphinx_automodapi
	pip install jupyter_sphinx
```
### Build the docs using the makefile
1. Make the docs.  In the `docs` directory
```
	make html
```
Congratulations!  The docs can now be found in your `docs\build\html` directory.
## View the Docs
Now that the docs are built you can access them via your browser.
You should be able to open the docs by just double clicking `index.html`. However if this does not work, try the following:
#### Manually
###### Chrome/Safari/Edge
Open your browser. While inside the browser, click ctrl + O (cmd + O on MacOs). You will see a file system pop up. Go to `docs\build\html\index.html`
Open `index.html` You should now see the docs.
#### Using Metal
Open a Python script or Jupyter Notebook. Write and run:
```
from qiskit_metal import open_docs
open_docs()
```