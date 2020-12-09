# Docs for Qiskit Metal

This folder contains the doc file src. We use sphinx to build the docs.

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

2. Install read [the docs theme](https://github.com/rtfd/sphinx_rtd_theme) and set in the config `html_theme = "sphinx_rtd_theme"`
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

### View the Docs
Now that the docs are built you can access them via your browser.

#### with chrome
Open Chrome while inside the browser, click ctrl + O (cmd + O on macos). You will see a file system pop up. Go to `docs\build\html\index.html`
Open `index.html` You should now see the docs.


#### with a local server
In your terminal/command prompt/powershell/etc cd into your `docs\build\html` folder and run
`python3 -m http.server`

Your should see `Serving HTTP on...`
Now open your browser and go to the link listed.
For example if yours says `Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...` then open your browser and put in `http://0.0.0.0:8000/` as the URL.

*It is important cd into the `html` folder before serving or else you will serve your entire folder directory.*
