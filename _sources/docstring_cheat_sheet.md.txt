# Docstring Cheat Sheet

Please refer to this for docstring help.

## Functions
```
""" 
Description of the function # These two lines appear on a single line in the output
More description
<blank line>                # Blank line inserts a new line
This text appears on a new line
<blank line>                # Blank line separates sections
Args:	# Don’t list if there are no arguments  # Arguments: is also acceptable
   Name1 (type): description                    # One argument per line
      Additional line of name1                  # Additional text must be indented
   Name2 (type): description. Defaults to value.   # Only list Default if there is a default value
   Name3 (type): description.
<blank line>                # Blank line separates sections
Returns:     # Don’t list if there is no return
   Type: Description                       # Only one return
   Additional line of return statement	   # NO indent for additional return text
<blank line>                               # Blank line separates sections
Raises:      # Don’t list if there are no raised exceptions
   Exception1: Reason it's raised
      Additional line of exception1        # Additional text must be indented
   Exception2: Reason it's raised
<blank line>                               # Blank line separates sections
Any other information you want to share    # Same text rules as Description section
"""
```

## Properties
```
""" 
Description of the property    # These two lines appear on a single line in the output
More description
<blank line>                   # Blank line inserts a new line
This text appears on a new line
"""
```

## Classes
### Part 1: under the class definition
```
class ClassName():
   """
   Description of the class     # These two lines appear on a single line in the output
   More description
   <blank line>                 # Blank line inserts a new line
   This text appears on a new line
   """
```

### Part 2: in the __init__ function
```
def __init__(self, <arguments here>):  
   """
   Additional description or details               # These two lines appear on a single line in the output
   More description
   <blank line>                                    # Blank line inserts a new line
   This text appears on a new line
   <blank line>                                    # Blank line separates sections
   Args:                                           # Don’t list if there are no arguments 
      Name1 (type): description                    # One argument per line
         Additional line of name1                  # Additional text must be indented
      Name2 (type): description. Defaults to value.   # Only list Default if there is a default value
      Name3 (type): description.
   """
```

## Formatting
| Format | Flag | Example |
| ------- | ------- | ------- |
| Bold | ** | `Regular **bold text** regular text again` |
| Italics | * | `Regular *italic text* regular text again` |
| Verbatim | `` | ```Interpreted ``as written`` interpreted again``` |
| Hyperlink | ` | ```Extends the `HairBand` class``` |

## Other stuff
Following all other rules defined above, you can insert these items as well.  Pay close attention to indentation so the docs display properly.

For simplicity, the sections below leave out the portions of the docstring above and below them.  Refer to the section above for those details.

### Custom selection
This will create a section (like the Args, Returns, or Raises).  Sections are nested to any depth.

```
This will create a section (like the Args, Returns, or Raises).  Sections are nested to any depth.
Section header:
   Section text              # These two lines appear on a single line in the output
   More section text
   <blank line>              # Blank line inserts a new line
   This text appears on a new line
<blank line>                 # Blank line separates sections
```

### Images
Note: the path assumes the image is located in the repository in the docs/apidocs directory of the repository.

```
.. image::
   image_file.png    # Note the indentation
<blank line>         # Blank line signifies end of image code
```

### Math
This will display mathematical expressions

```
.. math::
   <blank line>         # Blank line required
   \begin{split}
   x_\mathrm{off} &= x_0 - x_0 \cos{\theta} + y_0 \sin{\theta} \\
   y_\mathrm{off} &= y_0 - x_0 \sin{\theta} - y_0 \cos{\theta}
   \end{split}
<blank line>            # Blank line signifies end of math code
```

The code above will generate:

![Missing math image](https://github.com/Qiskit/qiskit-metal/blob/main/docs/images/math.jpg?raw=true "Math")

### Source code
Embed source code without executing it

```
.. code-block:: python
   :linenos:                # Optional: show line numbers
   :emphasize-lines: 2,4    # Optional: emphasize these lines (i.e. lines 2 and 4)
   <blank line>             # Blank line required
   Line of code
   Line of code
   Line of code
   Line of code
<blank line>                # Blank line signifies end of source code
```

### Ascii graphics (bulk verbatim)
Dump many lines verbatim – many times used for ascii graphics

```
::
   <blank line>         # Blank line required
   _________________
   |               |
   |_______________|       ^
   ________x________       |  N
   |               |       |
   |_______________|
<blank line>            # Blank line signifies end of bulk verbatim
```

### Lists
Create a bulleted

```
Section header:
   * first item             # These two lines appear on a single line in the output
     More first item text
   * second item            # Create as many items as you want
<blank line>                # Blank line signifies end of the list
```

### Caution flag
This will cause everything to highlight yellow with the text Caution above it

```
Caution:
   First line stuff to caution
   Section line of stuff to caution
<blank line>                # Blank line signifies end of the caution
```

### Warning flag
This will cause everything to highlight yellow with the text Warning above it

```
Warning:
   First line stuff to warn
   Section line of stuff to warn
<blank line>                # Blank line signifies end of the warning

```

