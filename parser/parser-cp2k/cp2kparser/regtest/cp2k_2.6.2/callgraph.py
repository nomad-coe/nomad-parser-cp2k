from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from cp2kparser import CP2KParser

with PyCallGraph(output=GraphvizOutput()):
    filepath = "/home/lauri/Dropbox/nomad-dev/nomad-lab-base/parsers/cp2k/test/unittests/cp2k_2.6.2/energy_force/unittest.out"
    parser = CP2KParser(filepath)
    parser.parse()
