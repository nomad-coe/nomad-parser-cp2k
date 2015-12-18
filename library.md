## NomadParser

The NomadParser class can be used as a base class for parsers in the NoMaD
project. The NomadParser class will automatically convert results to SI units,
format the results as JSON and push them to the backend. It will also validate
that the results match the type and shape defined for the quantity in the
metainfo file. A minimal example of a class that inherits NomadParser:

```python
class MyParser(NomadParser):
    """
    This class is responsible for setting up the actual parser implementation
    and provides the input and output for parsing. It inherits the NomadParser
    class to get access to many useful features.
    """
    def __init__(self, input_json_string):
        NomadParser.__init__(self, input_json_string)
        self.version = None
        self.implementation = None
        self.setup_version()
        # You would typically also setup some file id's here to help handling
        # the files. In this example the id's are already given in the JSON
        # input. To register a file you can call 'setup_file_id()'

    def start_parsing(self, name):
        """Asks the implementation object to give the result object by calling
        the function corresponding to the quantity name (=metaname). The
        NomadParser then automatically handles the conversion, validation and
        saving of the results.
        """
        return getattr(self.implementation, name)()

    def setup_version(self):
        """The parsers should be able to support different version of the same
        code. In this function you can determine which version of the software
        we're dealing with and initialize the correct implementation
        accordingly.
        """
        self.version = "1"
        self.implementation = globals()["MyParserImplementation{}".format(self.version)](self)

    def get_supported_quantities(self):
        return self.implementation.supported_quantities
```

The class MyParser only defines how to setup a parser based on the given input.
The actual dirty work is done by a parser implementation class. NomadParser
does not enforce any specific style for the implementation. By wrapping the
results in a Result object, you get the automatic unit conversion and JSON
backend support. A very minimal example of a parser implementation class:

```python
class MyParserImplementation1():
    """This is an implementation class that contains the actual parsing logic
    for a certain software version. There can be multiple implementation
    classes and MyParser decides which one to use.
    """
    supported_quantities = ["energy_total", "particle_forces", "particle_position"]

    def __init__(self, parser):
        self.parser = parser

    def energy_total(self):
        """Returns the total energy. Used to illustrate on how to parse a single
        result.
        """
        result = Result()
        result.unit = "joule"
        result.value = 2.0
        return result

    def particle_forces(self):
        """Returns multiple force configurations as a list. Has to load the
        entire list into memory. You should avoid loading very big files
        unnecessarily into memory. See the function 'particle_position()' for a
        one example on how to avoid loading the entire file into memory.
        """
        result = Result()
        result.unit = "newton"
        xyz_string = self.parser.get_file_contents("forces")
        forces = []
        i_forces = []
        for line in xyz_string.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith("i"):
                if i_forces:
                    forces.append(np.array(i_forces))
                    i_forces = []
                continue
            elif line.startswith("2"):
                continue
            else:
                i_forces.append([float(x) for x in line.split()[-3:]])
        if i_forces:
            forces.append(np.array(i_forces))
        result.value_iterable = forces
        return result

    def particle_position(self):
        """An example of a function returning a generator. This function does
        not load the whole position file into memory, but goes throught it line
        by line and returns configurations as soon as they are ready.
        """

        def position_generator():
            """This inner function is the generator, a function that remebers
            it's state and can yield intermediate results.
            """
            xyz_file = self.parser.get_file_handle("positions")
            i_forces = []
            for line in xyz_file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("i"):
                    if i_forces:
                        yield np.array(i_forces)
                        i_forces = []
                    continue
                elif line.startswith("2"):
                    continue
                else:
                    i_forces.append([float(x) for x in line.split()[-3:]])
            if i_forces:
                yield np.array(i_forces)

        result = Result()
        result.unit = "angstrom"
        result.value_iterable = position_generator()
        return result
```

The MyParser class decides which implementation to use based on e.g. the
software version number that is available on one of the input files. New
implementations corresponding to other software versions can then be easily
defined and they can also use the functionality of another implementation by
subclassing. Example:

```python
class MyParserImplementation2(MyParserImplementation1):
    """Implementation for a different version of the electronic structure
    software. Subclasses MyParserImplementation1. In this version the
    energy unit has changed and the 'energy' function from
    MyParserImplementation1 is overwritten.
    """

    def energy(self):
        """The energy unit has changed in this version."""
        result = Result()
        result.unit = "hartree"
        result.value = "2.0"
        return result
```
MyParser could be now used as follows:

```python
    input_json = """{
        "metaInfoFile": "metainfo.json",
        "tmpDir": "/home",
        "metainfoToKeep": [],
        "metainfoToSkip": [],
        "files": {
            forces.xyz": "forces",
            "positions.xyz": "positions"
        }
    }
    """

    parser = MyParser(json.dumps(input_json))
    parser.parse()
```

The input JSON string is used to initialize the parser. The 'metaInfoFile'
attribute contains the metainfo definitions used by the parser. From this file
the parser can determine the type and shape and existence of metainfo
definitions.

The 'files' object contains all the files that are given to the parser. The
attribute names are the file paths and their values are optional id's. The id's
are not typically given and they have to be assigned by using the
setup_file_id() function of NomadParser. Assigning id's helps to manage the
files.