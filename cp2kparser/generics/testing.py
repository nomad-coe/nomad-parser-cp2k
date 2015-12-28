"""
Tools for testing a nomad parser.
"""

import os
import json
import numpy as np


#===============================================================================
def get_parser(path, metainfopath, parserbuilderclass, stream):
    """Initialize a parser that is able to parse the contents in the given path.

    Args:
        path: String pointing to a path where all the calculation files are
        stream: The stream where the results are dumped.
        metainfopath: The metainfo filepath as a Get string
        parserbuilder: An object that inherits the ParserBuilder class and can
        create optimized parsers.
    """
    # Scan the given path for all files
    files = {}
    for filename in os.listdir(path):
        files[os.path.join(path, filename)] = ""

    json_input = {
        "version": "nomadparsein.json 1.0",
        "metaInfoFile": metainfopath,
        "metainfoToKeep": [],
        "metainfoToSkip": [],
        "files": files
    }
    parser = parserbuilderclass(json.dumps(json_input), stream=stream).build_parser()
    return parser


#===============================================================================
def get_metainfo(metaname, json_list):
    """After the parsing has been done by a parser, you can pass the resulting
    json list along with a metaname and the result will be returned to you.

    Args:
        metaname: String identifying a metainfo
        json_list: A json list object (see the python json package)
    """

    # Search for the metainfo
    # print json.dumps(json_list, sort_keys=True, indent=4, separators=(',', ': '))
    event_list = json_list[0]["events"]
    for event in event_list:
        name = event.get("metaName")
        if name and name == metaname:

            # Return value if present
            values = event.get("value")
            if values:
                return values

            # Return reshaped flatvalues if present
            flat_values = event.get("flatValues")
            shape = event.get("valuesShape")

            if flat_values and shape:
                shaped_values = np.reshape(flat_values, shape)
                return shaped_values
