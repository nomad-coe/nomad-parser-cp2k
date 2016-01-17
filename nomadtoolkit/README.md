# Nomad Toolkit
This a package that contains the necessary tools for running the nomad parsers
locally. It contains the python-common and nomad-meta-info repositories as
submodules for easier installation.

This package does not contain any of the parsers themselves. You should
download and install them separately. The parsers should have one main class
that inherits the 'Parser' baseclass and implements it's interface.

# Download
Currently this package is contained inside the parser-cp2k repository because
it is only used by it. If someones else want's to adopt these tools this
package can be maybe separated to it's own repository.

Use git to copy this repository to your local machine. You will also have to
recursively download the submodules. All this can be achieved with the command:

```sh
git clone --recursive git@gitlab.mpcdf.mpg.de:nomad-lab/parser-cp2k.git
```

# Installation
To install this toolkit run the included nomadtoolkit/setup.py file as follows:

```sh
python setup.py develop --user
```

# Usage

## Analysis
To access the parsed data locally you can use the Analyzer class. This class
will take care reading the parsed data and providing it to the user. The usage
is simple as:

```python
from nomadtoolkit import Analyzer
from cp2kparser import CP2KParser

dirpaths = "/home/lauri/Dropbox/nomad-dev/parser-cp2k/cp2kparser/cp2kparser/tests/cp2k_2.6.2/forces/outputfile/n"
parser = CP2KParser(contents=dirpaths)
analyzer = Analyzer(parser)
results = analyzer.parse()
```

The results class is now a dictionary where you can access any parsed quantity
by it's metainfo name. The metainfo viewer which is discussed next can help you
to identify what the available metainfo names are.

##Metainfo Viewer
The toolkit contains a browser based metainfo viewer for inspection of the
different metainfos. This tool is useful when the online resources are not
accessible. After succesfull installation you can start the viewer with the following command:

```sh
python -m nomadtoolkit -v
```

 This will open your default browser for viewing the metainfos.
