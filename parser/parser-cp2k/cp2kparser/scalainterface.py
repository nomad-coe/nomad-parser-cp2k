"""
This is the access point to the parser for the scala layer in the
NOMAD project.
"""
from __future__ import absolute_import
import sys
import setup_paths
from nomadcore.parsing.parser_backend import JsonParseEventsWriterBackend
from cp2kparser import CP2KParser


if __name__ == "__main__":

    # Initialise the parser with the main filename and a JSON backend
    main_file = sys.argv[1]
    parser = CP2KParser(backend=JsonParseEventsWriterBackend)
    parser.parse(main_file)
