from nomadanalysis import Analyzer
from cp2kparser import CP2KParser

# Initialize the parser you want to use
parser = CP2KParser()
parser.dirpath = "/home/lauri/Dropbox/nomad-dev/parser-cp2k/cp2kparser/cp2kparser/tests/cp2k_2.6.2/forces/outputfile/n"
parser.metainto_to_keep = ["section_run"]

# Initialize the analyzer
analyzer = Analyzer(parser)
results = analyzer.parse()
