# Dev Notes and decisions

## Structure 

`Metal_Design` is the very top object. 

### Rendered backends 
* extensions for specific objects

### Parsing options 
* all options should be string type 
* the strings are parse by a single function, which can interet them as variables, list, string, ints, floats with units 
 * Varaibles:  All strings that are [valid identifiers](https://docs.python.org/3/library/stdtypes.html?highlight=identifier#str.isidentifier), i.e., that could be interpretedas python variable names,  
  are assumed to be a variable. `'variable1'.isidentifier
 
