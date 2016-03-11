"""
This is the access point to the parser for the scala layer in the nomad project.
"""
import setup_paths
import os
from cp2kparser.parsing.versions.cp2k262.outputparser import CP2KOutputParser
from nomadcore.local_meta_info import loadJsonFile, InfoKindEl
from nomadcore.simple_parser import mainFunction

# This is what gets run when the scala layer calls for this parser. Version
# identification is skipped and the structure used in CP2K 2.6.2 is assumed.
if __name__ == "__main__":

    # Get the outputparser class
    outputparser = CP2KOutputParser(None, None)

    # Setup the metainfos
    metaInfoPath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../nomad-meta-info/meta_info/nomad_meta_info/cp2k.nomadmetainfo.json"))
    metaInfoEnv, warnings = loadJsonFile(filePath=metaInfoPath, dependencyLoader=None, extraArgsHandling=InfoKindEl.ADD_EXTRA_ARGS, uri=None)

    # Parser info
    parserInfo = {'name': 'cp2k-parser', 'version': '1.0'}

    # Adjust caching of metadata
    cachingLevelForMetaName = outputparser.caching_level_for_metaname

    # Supercontext is where the objet where the callback functions for
    # section closing are found
    superContext = outputparser

    # Main file description is the SimpleParser tree
    mainFileDescription = outputparser.root_matcher

    # Use the main function from nomadcore
    mainFunction(mainFileDescription, metaInfoEnv, parserInfo, superContext=superContext, cachingLevelForMetaName=cachingLevelForMetaName, onClose={})
