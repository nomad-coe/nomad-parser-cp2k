"""
When this package is run on a folder with python -m cp2kparser, the current
directory is searched for calculation data and the contents are parsed.
"""

import os
from cp2kparser.implementation.autoparser import parse_path
import argparse
import json

parser = argparse.ArgumentParser(description='Parse a CP2K calculation from folder.')
parser.add_argument('--metaInfoToKeep', type=str, help='A json list containing the names of the metainfos to keep during parsing.')
parser.add_argument('-dump', action='store_true')
args = parser.parse_args()

# Try to decode the metaInfoTokeep
metaInfoToKeep = []
if args.metaInfoToKeep:
    try:
        metaInfoToKeep = json.loads(args.metaInfoToKeep)
    except:
        raise Exception("Could not decode the 'metaInfoToKeep' argument as a json list. You might need to surround the string with single quotes if it contains double quotes.")

dump = args.dump

path = os.getcwd()
parse_path(path, metaInfoToKeep, dump)
