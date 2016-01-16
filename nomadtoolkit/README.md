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
