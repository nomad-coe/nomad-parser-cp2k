from nomadtoolkit import Analyzer
from cp2kparser import CP2KParser

# Initialize the parser you want to use. By default the parser will use the
# local backend. The local backend uses the metainfo files that come together
# with the nomadtoolkit repository and it outputs results in a python
# dictionary.
dirpaths = "/home/lauri/Dropbox/nomad-dev/parser-cp2k/cp2kparser/cp2kparser/tests/cp2k_2.6.2/forces/outputfile/n"
parser = CP2KParser(contents=dirpaths)

# Initialize the analyzer
analyzer = Analyzer(parser)
results = analyzer.parse()
# print results
