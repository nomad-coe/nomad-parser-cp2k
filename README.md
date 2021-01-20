This is a NOMAD parser for [CP2K](https://www.cp2k.org/). It will read CP2K input and
output files and provide all information in NOMAD's unified Metainfo based Archive format.

## Preparing code input and output file for uploading to NOMAD

NOMAD accepts `.zip` and `.tar.gz` archives as uploads. Each upload can contain arbitrary
files and directories. NOMAD will automatically try to choose the right parser for you files.
For each parser (i.e. for each supported code) there is one type of file that the respective
parser can recognize. We call these files `mainfiles` as they typically are the main
output file a code. For each `mainfile` that NOMAD discovers it will create an entry
in the database that users can search, view, and download. NOMAD will associate all files
in the same directory as files that also belong to that entry. Parsers
might also read information from these auxillary files. This way you can add more files
to an entry, even if the respective parser/code might not directly support it.

For CP2K please provide at least the files from this table if applicable to your
calculations (remember that you can provide more files if you want):



To create an upload with all calculations in a directory structure:

```
zip -r <upload-file>.zip <directory>/*
```

Go to the [NOMAD upload page](https://nomad-lab.eu/prod/rae/gui/uploads) to upload files
or find instructions about how to upload files from the command line.

## Using the parser

You can use NOMAD's parsers and normalizers locally on your computer. You need to install
NOMAD's pypi package:

```
pip install nomad-lab
```

To parse code input/output from the command line, you can use NOMAD's command line
interface (CLI) and print the processing results output to stdout:

```
nomad parse --show-archive <path-to-file>
```

To parse a file in Python, you can program something like this:
```python
import sys
from nomad.cli.parse import parse, normalize_all

# match and run the parser
archive = parse(sys.argv[1])
# run all normalizers
normalize_all(archive)

# get the 'main section' section_run as a metainfo object
section_run = archive.section_run[0]

# get the same data as JSON serializable Python dict
python_dict = section_run.m_to_dict()
```

## Developing the parser

Create a virtual environment to install the parser in development mode:

```
pip install virtualenv
virtualenv -p `which python3` .pyenv
source .pyenv/bin/activate
```

Install NOMAD's pypi package:

```
pip install nomad-lab
```

Clone the parser project and install it in development mode:

```
git clone https://github.com/nomad-coe/nomad-parser-cp2k.git nomad-parser-cp2k
pip install -e nomad-parser-cp2k
```

Running the parser now, will use the parser's Python code from the clone project.

## Parser Specific
## Usage notes
The parser is based on CP2K 2.6.2.

The CP2K input setting
[PRINT_LEVEL](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL.html#PRINT_LEVEL)
controls the amount of details that are outputted during the calculation. The
higher this setting is, the more can be parsed from the upload.

The parser will try to find the paths to all the input and output files, but if
they are located very deep inside some folder structure or outside the folder
where the output file is, the parser will not be able to locate them. For this
reason it is recommended to keep the upload structure as flat as possible.

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