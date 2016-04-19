"""
This is the access point to the parser for the scala layer in the
nomad project.
"""
import sys
import setup_paths
from nomadcore.parser_backend import JsonParseEventsWriterBackend
from cp2kparser import CP2KParser


if __name__ == "__main__":

    # Initialise the parser with the main filename and a JSON backend
    main_file = sys.argv[1]
    print main_file
    parser = CP2KParser(main_file, backend=JsonParseEventsWriterBackend)
    parser.parse()
