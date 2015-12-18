import os
import json
from cp2kparser.implementation.parser import CP2KParser
import sys


#===============================================================================
def scan_path_for_files(path):

    # Define the allowed extensions
    extensions = {
        ".inp",
        ".out",
        ".xyz",
        ".cif",
        ".pdb",
        ".dcd",
        ".cell",
        ".inc",
    }
    files = {}
    for filename in os.listdir(path):
        extension = os.path.splitext(filename)[1]
        if extension in extensions:
            files[os.path.join(path, filename)] = ""
    return files


#===============================================================================
def get_parser(path, test_mode=True, stream=sys.stdout):
    files = scan_path_for_files(path)
    metaInfoPath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../nomad-meta-info/meta_info/nomad_meta_info/cp2k.nomadmetainfo.json"))
    json_input = {
        "version": "nomadparsein.json 1.0",
        "metaInfoFile": metaInfoPath,
        "tmpDir": "/home",
        "metainfoToKeep": [],
        "metainfoToSkip": [],
        "files": files
    }
    parser = CP2KParser(json.dumps(json_input), test_mode=test_mode, stream=stream)
    return parser


#===============================================================================
if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))
    parser = get_parser(path)
    parser.parse()
