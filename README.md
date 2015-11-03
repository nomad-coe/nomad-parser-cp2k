# CP2K
The NoMaD parser for CP2K. Under development.

## QuickStart
- Clone repository
- Run setup by running the setup.py script:
    $ python setup.py install --user
- Run tests (TODO)

## Structure
Currently the python package is divided into three subpackages:
 - Engines: Classes for parsing different type of files
 - Generics: Generic utility classes and base classes
 - Implementation: The classes that actually define the parser functionality.
