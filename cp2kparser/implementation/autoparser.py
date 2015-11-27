import os
import json
from cp2kparser.implementation.parser import CP2KParser


#===============================================================================
def scan_path_for_files(path):

    # Define the allowed extensions
    extensions = {
        ".inp",
        ".out",
        ".xyz",
        ".cif",
        ".pdb",
    }
    files = {}
    for filename in os.listdir(path):
        extension = os.path.splitext(filename)[1]
        if extension in extensions:
            files[os.path.join(path, filename)] = ""
    return files


#===============================================================================
def get_parser(path, test=True):
    files = scan_path_for_files(path)
    json_input = {
        "version": "nomadparsein.json 1.0",
        "tmpDir": "/home/lauri",
        "metainfoToKeep": [],
        "metainfoToSkip": [],
        "files": files
    }
    parser = CP2KParser(json.dumps(json_input), test=test)
    return parser


#===============================================================================
if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))
    parser = get_parser(path)
    parser.parse_all()
