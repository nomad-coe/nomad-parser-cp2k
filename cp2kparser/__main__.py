import os
from cp2kparser.implementation.autoparser import parse_path
import argparse
import json

parser = argparse.ArgumentParser(description='Parse a CP2K calculation from folder.')
parser.add_argument('-metaInfoToKeep', type=str, help='A json list containing the names of the metainfos to keep during parsing.')
parser.add_argument('-metaInfoToSkip', type=str, help='A json list containing the names of the metainfos to skip during parsing.')
args = parser.parse_args()

# Try to decode the metaInfoTokeep
metaInfoToKeep = []
if args.metaInfoToKeep:
    try:
        metaInfoToKeep = json.loads(args.metaInfoToKeep)
    except:
        raise Exception("Could not decode the 'metaInfoToKeep' argument as a json list. You might need to surround the string with single quotes if it contains double quotes.")

# Try to decode the metaInfoToSkip
metaInfoToSkip = []
if args.metaInfoToSkip:
    try:
        metaInfoToSkip = json.loads(args.metaInfoToSkip)
    except:
        raise Exception("Could not decode the 'metaInfoToKeep' argument as a json list. You might need to surround the string with single quotes if it contains double quotes.")

path = os.getcwd()
parse_path(path, metaInfoToKeep, metaInfoToSkip)
