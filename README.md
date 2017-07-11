This is the main repository of the [NOMAD](http://nomad-lab.eu) parser for
[CP2K](https://www.cp2k.org/).

# Example
```python
    from cp2kparser import CP2KParser
    import matplotlib.pyplot as mpl

    # 1. Initialize a parser by giving a path to the CP2K output file and a list of
    # default units
    path = "path/to/main.file"
    default_units = ["eV"]
    parser = CP2KParser(path, default_units=default_units)

    # 2. Parse
    results = parser.parse()

    # 3. Query the results with using the id's created specifically for NOMAD.
    scf_energies = results["energy_total_scf_iteration"]
    mpl.plot(scf_energies)
    mpl.show()
```

# Installation
The code is python>=2.7 and python>=3.4 compatible. First download and install
the nomadcore package:

```sh
git clone https://gitlab.mpcdf.mpg.de/nomad-lab/python-common.git
cd python-common
pip install -r requirements.txt
pip install -e .
```

Download and install the parser:

```sh
git clone https://gitlab.mpcdf.mpg.de/nomad-lab/parser-cp2k.git
cd parser-cp2k
pip install -e .
```

# Advanced

The parser is designed to support multiple versions of CP2K with a [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
approach: The initial parser class is based on CP2K 2.6.2, and other versions
will be subclassed from it. By sublassing, all the previous functionality will
be preserved, new functionality can be easily created, and old functionality
overridden only where necesssary.

# Upload Folder Structure, File Naming and CP2K Settings
The CP2K input setting
[PRINT_LEVEL](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL.html#PRINT_LEVEL)
controls the amount of details that are outputted during the calculation. The
higher this setting is, the more can be parsed from the upload.

The parser will try to find the paths to all the input and output files, but if
they are located very deep inside some folder structure or outside the folder
where the output file is, the parser will not be able to locate them. For this
reason it is recommended to keep the upload structure as flat as possible.

## Testing
The regression tests for this parser are located in
**/cp2k/parser/parser-cp2k/cp2kparser/regtest**. You can run the tests by
running the run_tests.py file in one of the version directories.

## Notes for CP2K Developers
Here is a list of features/fixes that would make the parsing of CP2K results
easier:
 - The pdb trajectory output doesn't seem to conform to the actual standard as
   the different configurations are separated by the END keyword which is
   supposed to be written only once in the file. The [format
   specification](http://www.wwpdb.org/documentation/file-format) states that
   different configurations should start with MODEL and end with ENDMDL tags.
 - The output file should contain the paths/filenames of different input and
   output files that are accessed during the program run. This data is already
   available for some files (input file, most files produced by MD), but many
   are not mentioned.
