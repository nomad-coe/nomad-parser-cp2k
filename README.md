# CP2K
The NoMaD parser for CP2K. Under development. Will be modified to conform to
the common parser structure when it is available.

## QuickStart
- Clone repository
- Run setup by running the setup.py script. For local, user specific install
  without sudo permissions use:

    ```shell
    python setup.py install --user
    ```

  For a system-wide install use:

    ```shell
    python setup.py install
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

## Structure
Currently the python package is divided into three subpackages:
 - Engines: Classes for parsing different type of files
 - Generics: Generic utility classes and base classes
 - Implementation: The classes that actually define the parser functionality.

## Reusable components and ideas for other parsers

Some components and ideas could be reused in other parsers as well. If you find
any of the following useful in you parser, you are welcome to do so.

### Engines
Basically all the "engines", that is the modules that parse certain type of
files, are reusable as is in other parsers. They could be put into a common
repository where other developers can improve and extend them. One should also
write tests for the engines that would validate their behaviour and ease the
performance analysis.

Currently implemented engines that could be reused (not tested properly yet):
- RegexEngine: For parsing text files with regular expressions. Uses the re2
  library if available (falls back to default python regex implementation if
  re2 not found).
- XyzEngine: For parsing XYZ files and files with similar structure. Has a very
  flexible nature as you can specify comments, column delimiters, column
  indices and the patterns used to separate different configurations.

### NomadParser base class
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

## Lessons learned

