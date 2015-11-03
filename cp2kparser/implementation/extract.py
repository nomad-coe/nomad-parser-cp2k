import logging
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
    }
    files = []
    for filename in os.listdir(path):
        extension = os.path.splitext(filename)[1]
        if extension in extensions:
            file_object = {
                "path": filename,
                "file_id": "",
            }
            files.append(file_object)
    return files


#===============================================================================
def extract(path):
    files = scan_path_for_files(path)
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    json_input = {
        "version": "nomadparsein.json 1.0",
        "tmpDir": "/home/lauri",
        "metainfoToKeep": [],
        "metainfoToSkip": [],
        "files": files
    }
    parser = CP2KParser(json.dumps(json_input))
    print parser.get_quantity("energy_total")
    print parser.get_quantity("XC_functional")
    print parser.get_quantity("particle_forces")
    # n = len(parser.get_quantity("particle_forces"))
    # print "Number of force configurations found: {}".format(n)
