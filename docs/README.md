# Docs for Qiskit Metal
In the future, users will not need to build their own docs. However, during early-access, these docs must be built by the user.
This folder contains the doc file src. We use sphinx to build the docs. _Docs may take up to 15 minutes to build._
## The automated method
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
2. Install read [the docs theme](https://github.com/rtfd/sphinx_rtd_theme) and set in the config `html_theme = “sphinx_rtd_theme”`
```
	pip install sphinx_rtd_theme
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