# CP2K NoMaD Parser

# QuickStart
- Clone repository

    ```shell
    git clone git@gitlab.mpcdf.mpg.de:nomad-lab/parser-cp2k.git
    ```

- Run setup by running the setup.py script. For local, user specific install
  without sudo permissions use (omit --user for a system-wide install):

    ```shell
    python setup.py install --user
    ```

- You can test if everything is running fine by running the test script in tests folder:

    ```shell
    cd cp2kparser/tests/cp2k_2.6.2
    python run_tests.py
    ```

- If you want to try out parsing for a custom cp2k calculation, place all
  relevant output and input files inside a common directory and run the
  following command within that folder:

    ```shell
    python -m cp2kparser
    ```

# Structure
Currently the python package is divided into three subpackages:
- Engines: Classes for parsing different type of files
- Generics: Generic utility classes and base classes
- Implementation: The classes that actually define the parser functionality.

## Engines
Basically all the "engines", that is the modules that parse certain type of
files, are reusable in other parsers. They could be put into a common
repository where other developers can improve and extend them. One should also
write tests for the engines that would validate their behaviour and ease the
performance analysis.

The engine classes work also as interfaces. You can change the engine behaviour
while maintaining the same API in the parsers. For example one might improve
the performance of an engine but if the function calls remain the same no other
code has to be changed.

Currently implemented engines that could be reused (not tested properly yet):
- AtomsEngine: For reading various atomic coordinate files. Currently uses ASE
  to read the files.
- RegexEngine: For parsing text files with regular expressions. Uses the re2
library if available (falls back to default python regex implementation if
re2 not found).
- CSVEngine: For parsing CSV-like files. Has a very
flexible nature as you can specify comments, column delimiters, column
indices and the patterns used to separate different configurations.
- XMLEngine: For parsing XML files using XPath syntax.

## Generics
In the generics folder there is a module called nomadparser.py that defines a
class called NomadParser. This acts as a base class for the cp2k parser defined
in the implementation folder.

The NomadParser class defines the interface which is eventually used by e.g.
the scala code (will be modified later to conform to the common interface).
This class is also responsible for some common tasks that are present in all
parsers:

- Unit conversion
- JSON encoding
- Caching
- Time measurement for performance analysis
- Providing file contents, sizes and handles

# Tools and Methods

The following is a list of tools/methods that can help the development process.

## Documentation
The [google style guide](https://google.github.io/styleguide/pyguide.html?showone=Comments#Comments) provides a good template on how to document your code.
Documenting makes it much easier to follow the logic behind your parser.

## Logging
Python has a great [logging
package](https://docs.python.org/2/library/logging.html) which helps in
following the program flow and catching different errors and warnings. In
cp2kparser the file cp2kparser/generics/logconfig.py defines the behaviour of
the logger. There you can setup the log levels even at a modular level. A more
easily readable formatting is also provided for the log messages.

## Testing
The parsers can become quite complicated and maintaining them without
systematic testing can become troublesome. Unit tests provide one way to
test each parseable quantity and python has a very good [library for
unit testing](https://docs.python.org/2/library/unittest.html). When the parser
supports a new quantity it is quite fast to create unit tests for it. These
tests will validate the parsing, and also easily detect bugs that may rise when
the code is modified in the future.

## Unit conversion
You can find unit conversion tools from the python-common repository and its
nomadcore package.  The unit conversion is currenlty done by
[Pint](https://pint.readthedocs.org/en/0.6/) and it has a very natural syntax,
support for numpy arrays and an easily reconfigurable constant/unit declaration
mechanisms.

## Profiling
The parsers have to be reasonably fast. For some codes there is already
significant amount of data in the NoMaD repository and the time taken to parse
it will depend on the performance of the parser. Also each time the parser
evolves after system deployment, the existing data may have to be reparsed at
least partially.

By profiling what functions take the most computational time and memory during
parsing you can identify the bottlenecks in the parser. There are already
existing profiling tools such as
[cProfile](https://docs.python.org/2/library/profile.html#module-cProfile)
which you can plug into your scripts very easily.

# Manual for uploading a CP2K calculation
The print level (GLOBAL/PRINT_LEVEL) of a CP2K run will afect how much
information can be parsed from it. Try to use print levels MEDIUM and above to
get best parsing results.

All the files that are needed to run the calculation should be included in the
upload, including the basis set and potential files. The folder structure does
not matter, as the whole directory is searced for relevant files.

Although CP2K often doesn't care about the file extensions, using them enables
the parser to automatically identify the files and makes it perform better
(only needs to decompress part of files in HDF5). Please use these default file
extensions:
 - Output file: .out (Only one)
 - Input file: .inp (Only one. If you have "include" files, use some other extension e.g. .inc)
 - XYZ coordinate files: .xyz
 - Protein Data Bank files: .pdb
 - Crystallographic Information Files: .cif

# Notes for CP2K developers
Here is a list of features/fixes that would make the parsing of CP2K results
easier:
 - The pdb trajectory output doesn't seem to conform to the actual standard as
   the different configurations are separated by the END keyword which is
   supposed to be written only once in the file. The [format specification](http://www.wwpdb.org/documentation/file-format)
   states that different configurations should start with MODEL and end with
   ENDMDL tags.
