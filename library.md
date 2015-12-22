## More Complex Parsing Scenarios

The utilities in simple_parser.py can be used alone to make a parser in many
cases. The SimpleMatchers provide a very nice declarative way to define the
parsing process and takes care of unit conversion and pushing the results to
the scala layer.

Still you may find it useful to have additional help in handling more complex
scenarios. During the parser development you may encounter these questions:
    - How to manage different versions fo the parsed code that may even have completely different syntax?
    - How to handle multiple files?
    - How to integrate all this with the functionality that is provided in simple_parser.py?

The NomadParser class is meant help in structuring your code. It uses the same
input and output format as the mainFunction in simple_parser.py. Here is a
minimal example of a parser that subclasses NomadParser Here is a minimal
example of a parser that subclasses NomadParser:

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

    def setup_version(self):
        """The parsers should be able to support different version of the same
        code. In this function you can determine which version of the software
        we're dealing with and initialize the correct implementation
        accordingly.
        """
        self.version = "1"
        self.implementation = globals()["MyParserImplementation{}".format(self.version)](self)

    def parse(self):
        """After the version has been identified and an implementation is
        setup, you can start parsing.
        """
        return getattr(self.implementation, name)()
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
