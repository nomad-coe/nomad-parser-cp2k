import sys
import os
import cStringIO
from cp2kparser.implementation.cp2kparserversioner import CP2KParserVersioner
from cp2kparser.generics.testing import get_parser


#===============================================================================
def parse_path(path, metainfo_to_keep=[], metainfo_to_skip=[], dump=False):
    """Generates a cp2k parser using the tools defined in testing.py and parses
    the contents in the given path
    """
    # If a dump is requested, the results will be saved to a file under the
    # current folder
    if dump:
        stream = cStringIO.StringIO()
    else:
        stream = sys.stdout
    parserbuilder = CP2KParserVersioner
    metainfopath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../nomad-meta-info/meta_info/nomad_meta_info/cp2k.nomadmetainfo.json"))
    parser = get_parser(path, metainfopath,  parserbuilder, metainfo_to_keep, metainfo_to_skip, stream)
    parser.parse()

    if dump:
        outputfile = open(path + "/parseroutput.json", "w")
        outputfile.write(stream.getvalue())
