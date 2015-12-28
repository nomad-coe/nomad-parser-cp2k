import json
import logging
from nomadcore.parser_backend import JsonParseEventsWriterBackend
from nomadcore.local_meta_info import loadJsonFile
from abc import ABCMeta, abstractmethod
logger = logging.getLogger(__name__)


#===============================================================================
class ParserVersioner(object):
    """Class that sets up a version specific parser implementation based on the
    given files.

    To initialize a ParserVersioner, you need to give it a JSON string in the
    constructor. JSON is used because it is language-agnostic and can easily
    given as a run argument for the parser. An example of the JSON file might
    look like this:

        {
            "metaInfoFile": "/home/metainfo.json"
            "metainfoToKeep": ["energy"],
            "metainfoToSkip": ["particle_forces"],
            "files": {
                "/home/output.out": "output",
                "/home/input.inp": "input",
                "/home/coords.xyz": ""
            }
        }

    Here is an explanation of the different attributes:
        - metaInfoFile: The metainfo JSON file path containing the metainfo definitions
          used by this parser
        - metainfoToKeep: What metainfo should be parsed. If empty, tries to
          parse everything except the ones specified in 'metainfoToSkip'
        - metainfoToSkip: A list of metainfos that should be ignored
        - files: Dictionary of files. The key is the path to the file, and the
          value is an optional identifier that can be provided or later
          determined by the parser. The identifier might prove useful if the
          uploader can manually assign ids to files.

    Attributes:
        input_json_string: A string containing the JSON input.
        files: A dictionary of file paths as keys and id's as values. These ids's only include
        the ones given at initialization in the input JSON.
        meta_info_to_keep: The metainfo names to keep
        meta_info_to_skip: The metainfo names to skip
        backend: An object responsible for the JSON formatting and sending the
        results to the scala layer.
        version_override: An object that is used to force a specific version.
        Can be e.g. a string that identifies a version.
    """
    __metaclass__ = ABCMeta

    def __init__(self, input_json_string, stream, version_override=None):
        """
        """
        self.input_json_string = input_json_string
        self.parser_context = ParserContext()
        self.parser_context.stream = stream
        self.parser_context.version_id = version_override
        self.analyze_input_json()

    def analyze_input_json(self):
        """Analyze the validity of the JSON string given as input.
        """
        # Try to decode the input JSON
        try:
            input_json_object = json.loads(self.input_json_string)
        except ValueError as e:
            logger.error("Error in decoding the given JSON input: {}".format(e))

        # See if the needed attributes exist
        metainfo_file = input_json_object.get("metaInfoFile")
        if metainfo_file is None:
            logger.error("No metainfo file path specified.")
        self.parser_context.files = input_json_object.get("files")
        if self.parser_context.files is None:
            logger.error("No files specified.")
        self.parser_context.metainfo_to_keep = input_json_object.get("metainfoToKeep")
        self.parser_context.metainfo_to_skip = input_json_object.get("metainfoToSkip")

        # Try to decode the metainfo file and setup the backend
        self.parser_context.metainfoenv, self.parser_context.metainfowarnings = loadJsonFile(metainfo_file)
        self.parser_context.backend = JsonParseEventsWriterBackend(self.parser_context.metainfoenv, self.parser_context.stream)

    @abstractmethod
    def build_parser(self):
        """Deduce the version of the software that was used and setup a correct
        implementation. The implementations should subclass NomadParser.

        Returns:
            A NomadParser object that is ready to do the parsing.
        """
        pass


#===============================================================================
class ParserContext(object):
    """Contains everything needed to instantiate a parser implementation.
    """
    def __init__(self, version_id=None, files=None, metainfoenv=None, metainfowarnings=None, metainfo_to_keep=None, metainfo_to_skip=None, backend=None, stream=None):
        self.version_id = version_id
        self.metainfoenv = metainfoenv
        self.metainfowarnings = metainfowarnings
        self.metainfo_to_keep = metainfo_to_keep
        self.metainfo_to_skip = metainfo_to_skip
        self.files = files
        self.backend = backend
        self.stream = stream
