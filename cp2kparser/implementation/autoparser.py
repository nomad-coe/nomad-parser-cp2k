import sys
import os
from cp2kparser.implementation.cp2kparserversioner import CP2KParserVersioner
from cp2kparser.generics.testing import get_parser


#===============================================================================
def parse_path(path, metainfo_to_keep=[], metainfo_to_skip=[]):
    """Generates a cp2k parser using the tools defined in testing.py and parses
    the contents in the given path
    """
    parserbuilder = CP2KParserVersioner
    metainfopath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../nomad-meta-info/meta_info/nomad_meta_info/cp2k.nomadmetainfo.json"))
    parser = get_parser(path, metainfopath,  parserbuilder, metainfo_to_keep, metainfo_to_skip, sys.stdout)
    parser.parse()
