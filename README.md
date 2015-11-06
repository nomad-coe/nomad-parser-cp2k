# CP2K
The NoMaD parser for CP2K. Under development. Will be modified to conform to
the common parser structure when it is available.

## QuickStart
- Clone repository
- Run setup by running the setup.py script:
    $ python setup.py install --user
- Parsing can be currently tested by simply running the script "parse.py" in a folder

## Structure
Currently the python package is divided into three subpackages:
 - Engines: Classes for parsing different type of files
 - Generics: Generic utility classes and base classes
 - Implementation: The classes that actually define the parser functionality.
