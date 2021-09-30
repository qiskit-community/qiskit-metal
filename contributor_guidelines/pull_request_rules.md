# Pull Request content guidelines

## New components or updating existing components

You have worked hard and updated a component code or created your custom component (a class that directly or indirectly inherits the `QComponent` class and implements the `make()` method). Now you would like to showcase your work in Qiskit Metal, for everyone to see and use. So what do you need to do?

The first step is to put your code in a github branch or fork, and then create a Pull Request, to propose the new code to be added to the main repository. But is your code all that is needed to properly showcase your work?

Documentation plays the most important part in your showcase, and unit-test plays the most important part in making sure your work is functional and nobody else can change your intended behavior. So let's add these two pieces:

### Add the circuit example notebook to the QComponent documentation
1. Create the notebook in the tutorials folder
    1. Make sure it only contains the QComponent rendering lines, unless any other "unique" behavior is worth highlighting
    1. Make sure the cell outputs are "cleared"
1. Add the notebook to the toc (table of content)
    1. Open `qiskit_metal/qlibrary/__init__.py`
        1. add the QComponent class name to the most appropriate toc-tree
        1. locate the `if config.is_building_docs():` and inside it add the import for the new QComponent.
    1. Edit and execute the `docs/_utility/generate_images.ipynb` to include the new component and generate its icon image for the doc notebook
1. Create the notebook in the doc examples folder
    1. Copy, execute and save the tutorial QComponent notebook (Step 1) to the doc/circuit-examples
    1. Enable the tags: View -> Cell toolbar -> tags
    1. Find the cell that contains the image generation: `gui.figure.savefig('shot.png') ...` . If you do not have it in the notebook, please check other notebooks in this folder and mimic them.
        - Add to this cell the tag nbsphinx-thumbnail
1. Run the doc build locally to update the apidocs folder files
1. Commit back to the PR


### Add the unit-test for the new QComponent
1. Add the instantiation test for the new component inside file `test_qlibrary_1_instantiate.py`:
    1. Add an import towards the top of the file for the new component class
    1. Create a method to test the instance. You can use as a template the method `test_qlibrary_qubits_transmon_pocket()`
1. Add the options test for the new component inside file `test_qlibrary_2_options.py`:
    1. Add an import towards the top of the file for the new component class
    1. Create a method to test the options. You can use as a template the method `test_qlibrary_transmon_concentric_options()`
1. Add the functionality test for the new component inside file `test_qlibrary_3_functionality.py`:
    1. Add an import towards the top of the file for the new component class
    1. If needed, create a method to test the metadata. You can use as a template the method `test_qlibrary_transmon_pocket_component_metadata()`
    1. Add any other functional test that you deem appropriate