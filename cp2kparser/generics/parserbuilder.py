import json
import logging
from nomadcore.parser_backend import JsonParseEventsWriterBackend
from nomadcore.local_meta_info import loadJsonFile
import sys
from abc import ABCMeta, abstractmethod
logger = logging.getLogger(__name__)


#===============================================================================
class ParserBuilder(object):
    """Class that sets up a parser implementation based on the given files and
    the metainfos to include/exclude.

    To initialize a ParserBuilder, you need to give it a JSON string in the
    constructor. JSON is used because it is language-agnostic and can easily given
    as a run argument for the parser. An example of the JSON file might look like
    this:

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
          determined by the parser.

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

    def __init__(self, input_json_string, stream=sys.stdout, version_override=None):
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









    # def setup_given_file_ids(self):
        # """Saves the file id's that were given in the JSON input.
        # """
        # for path, file_id in self.files.iteritems():
            # if file_id:
                # self.setup_file_id(path, file_id)

    # @abstractmethod
    # def parse(self):
        # """Start the parsing. Will try to parse everything unless given special
        # rules (metaInfoToKeep, metaInfoToSkip)."""
        # pass

    # def parse_file(
            # self,
            # fileToParse,
            # mainFileDescription,
            # metaInfoEnv,
            # backend,
            # parserInfo,
            # cachingLevelForMetaName={},
            # defaultDataCachingLevel=CachingLevel.ForwardAndCache,
            # defaultSectionCachingLevel=CachingLevel.Forward,
            # superContext=None,
            # onClose={}):
        # """Uses the SimpleParser utilities to to parse a file.

        # Args:
        # Returns:
        # """
        # # Initialize the parser builder
        # parserBuilder = SimpleParserBuilder(mainFileDescription, metaInfoEnv)
        # if logger.isEnabledFor(logging.DEBUG):
            # s = StringIO.StringIO()
            # s.write("matchers:")
            # parserBuilder.writeMatchers(s, 2)
            # logger.debug(s.getvalue())

        # # Verify the metainfo
        # if not parserBuilder.verifyMetaInfo(sys.stderr):
            # sys.exit(1)

        # # Setup the backend that caches ond handles triggers
        # backend = ActiveBackend.activeBackend(
            # metaInfoEnv=metaInfoEnv,
            # cachingLevelForMetaName=cachingLevelForMetaName,
            # defaultDataCachingLevel=defaultDataCachingLevel,
            # defaultSectionCachingLevel=defaultSectionCachingLevel,
            # onClose=onClose,
            # superBackend=backend)

        # # Compile the SimpleMatcher tree
        # parserBuilder.compile()
        # if logger.isEnabledFor(logging.DEBUG):
            # s = StringIO.StringIO()
            # s.write("compiledMatchers:")
            # parserBuilder.writeCompiledMatchers(s, 2)
            # logger.debug(s.getvalue())

        # writeComma = False
        # outF = sys.stdout
        # parse_function = defaultParseFile(parserInfo)
        # uri = None
        # if uri is None and fileToParse:
            # uri = "file://" + fileToParse
        # if fileToParse:
            # if writeComma:
                # outF.write(", ")
            # else:
                # writeComma = True
            # parse_function(parserBuilder, uri, fileToParse, backend, self)

    # def setup_file_id(self, path, file_id):
        # """Used to map a simple identifier string to a file path. When a file
        # id has been setup, you can easily access the file by using the
        # functions get_file_handle() or get_file_contents()
        # """
        # if path in self.files:
            # value = self.file_ids.get(file_id)
            # if value:
                # value.append(path)
            # else:
                # pathlist = []
                # pathlist.append(path)
                # self.file_ids[file_id] = pathlist
        # else:
            # logger.error("Trying to setup an id for an undefined path. See that the path was written correctly and it was given in the files attribute of the JSON string.")

    # def get_filepath_by_id(self, file_id):
        # """Get the file paths that were registered with the given id.
        # """
        # value = self.file_ids.get(file_id)
        # if value:
            # if isinstance(value, list):
                # n = len(value)
                # if n == 1:
                    # return value[0]
                # elif n == 0:
                    # logger.warning("No files set with id '{}'".format(file_id))
                    # return None
                # else:
                    # logger.debug("Multiple files set with id '{}'".format(file_id))
                    # return value
        # else:
            # logger.warning("No files set with id '{}'".format(file_id))

    # def get_file_handle(self, file_id):
        # """Get the handle for a single file with the given id. Uses cached result
        # if available. Always seeks to beginning of file before returning it.
        # """
        # # Get the filepath(s)
        # path = self.get_filepath_by_id(file_id)
        # if not path:
            # logger.warning("No filepaths registered to id '{}'. Register id's with setup_file_id().".format(file_id))
            # return

        # if isinstance(path, list):
            # if len(path) == 0:
                # return
            # elif len(path) != 1:
                # logger.error("Multiple filepaths found with id '{}'. Use get_file_handles() instead if you expect to have multiple files.".format(file_id))
                # return
            # else:
                # path = path[0]

        # # Search for filehandles, if not present create one
        # handle = self._file_handles.get(path)
        # if not handle:
            # try:
                # handle = open(path, "r")
            # except (OSError, IOError):
                # logger.error("Could not open file: '{}'".format(path))
            # else:
                # self._file_handles[file_id] = handle
        # handle.seek(0, os.SEEK_SET)
        # return handle

    # def get_file_handles(self, file_id):
        # """Get the handles for multiple files with the given id. Uses cached result
        # if available. Always seeks to beginning of files before returning them.
        # """
        # # Get the filepath(s)
        # paths = self.get_filepath_by_id(file_id)
        # if not paths:
            # return
        # if not isinstance(paths, list):
            # paths = [paths]

        # # Search for filehandles, if not present create one
        # handles = []
        # for path in paths:
            # handle = self._file_handles.get(path)
            # if not handle:
                # try:
                    # handle = open(path, "r")
                # except (OSError, IOError):
                    # logger.error("Could not open file: '{}'".format(path))
                # else:
                    # self._file_handles[file_id] = handle
            # handle.seek(0, os.SEEK_SET)
            # handles.append(handle)

        # # Return handles
        # if len(handles) == 0:
            # return None
        # else:
            # return handles

    # def get_file_contents(self, file_id):
        # """Get the contents for the file with the given id. Uses cached result
        # if available. Does not cache files that are bigger than a certain
        # limit.
        # """
        # cache_limit = 10000
        # contents = self._file_contents.get(file_id)
        # if not contents:
            # fh = self.get_file_handle(file_id)
            # fh.seek(0)
            # contents = fh.read()
            # if self.get_file_size(file_id) <= cache_limit:
                # self._file_contents[file_id] = contents
        # return contents

    # def get_file_size(self, file_id):
        # """Get the size of a file with the given id. Uses cached result
        # if available.
        # """
        # size = self._file_sizes.get(file_id)
        # if not size:
            # fh = self.get_file_handle(file_id)
            # fh.seek(0, os.SEEK_END)
            # size = fh.tell()
            # self._file_sizes[file_id] = size
        # return size

    # @abstractmethod
    # def get_supported_quantities(self):
        # """Return a list of the nomad quantities that this parser supports. The
        # list should contain the metaInfoNames of the supported quantities.
        # """
        # pass

    # @abstractmethod
    # def start_parsing(self, name):
        # """Start parsing the given quantity and outputs the result to the
        # backend.

        # There are two modes of operation:

            # automatic: If this function returns a Result object, the function
            # parse_quantity will detect it, convert the units, format the
            # result to JSON and send it to the backend. Supports also returning
            # iterators that yield multiple results (handy for generator
            # functions that loop over e.g. a trajectory file extracting the
            # trajectory one configuration at a time without reading the entire
            # file into memory).

            # manual: You use the backend explicitly and do the unit
            # conversion and JSON formatting "manually". In this case the
            # function should return 'None'.
        # """
        # pass

    # def check_quantity_availability(self, name):
        # """Check if the given quantity can be parsed with this parser setup.
        # Checks through the list given by get_supported_quantities and also
        # checks the metainfoToSkip parameter given in the JSON input.
        # """
        # if name not in self.get_supported_quantities():
            # return False
        # if name in self.metainfo_to_skip:
            # logger.error("The metaname '{}' cannot be calculated as it is in the list 'metaInfoToSkip'.".format(name))
            # return False
        # return True

    # def parse(self):
        # """Start parsing the contents.
        # """
        # # Determine which values in metainfo are parseable
        # metainfos = self.metainfos.itervalues()
        # for metainfo in metainfos:
            # name = metainfo["name"]
            # if self.check_quantity_availability(name):
                # self.parse_quantity(name)

    # def parse_quantity(self, name):
        # """Given a unique quantity id (=metaInfo name) which is supported by
        # the parser, parses the corresponding quantity (if available), converts
        # it to SI units and return the value as json.
        # """

        # logger.info("GETTING QUANTITY '{}'".format(name))

        # #Check availability
        # available = self.check_quantity_availability(name)
        # if not available:
            # return

        # # Get the result by parsing or from cache
        # result = self.get_result_object(name)

        # if result is not None:
            # if isinstance(result, Result):
                # if not self.test_mode:
                    # metainfo = self.metainfos.get(name)
                    # result.name = name
                    # result.dtypstr = metainfo.get("dtypeStr")
                    # result.repeats = metainfo.get("repeats")
                    # result.shape = metainfo.get("shape")
                    # self.result_saver(result)
                # # In test mode just return the values directly
                # else:
                    # if result.value is not None:
                        # if result.value_iterable is None:
                            # return result.value
                    # elif result.value_iterable is not None:
                        # values = []
                        # for value in result.value_iterable:
                            # values.append(value)
                        # values = np.array(values)
                        # if values.size != 0:
                            # return values

    # def get_result_object(self, name):
        # # Check cache
        # result = self.results.get(name)
        # if result is None:
            # result = self.start_parsing(name)
            # if result:
                # if result.cache:
                    # self.results[name] = result
        # return result

    # def result_saver(self, result):
        # """Given a result object, saves the results to the backend.

        # The numeric results are automatically converted to SI units if a unit
        # has been defined. Automatic conversion to the correct data type
        # defined in the metainfo is attempted.
        # """
        # name = result.name
        # value = result.value
        # unit = result.unit
        # value_iterable = result.value_iterable
        # repeats = result.repeats
        # dtypestr = result.dtypstr
        # shape = result.shape

        # # Save a single result
        # if value is not None:
            # if value_iterable is None:
                # if repeats:
                    # logger.error("A repeating value was given in Result.value. Repeating values should be stored in Result.value_iterable instead.")
                    # return

                # # Save to backend
                # section_id = self.backend.openSection(name)
                # self.input_value_to_backend(name, value, unit, dtypestr, shape)
                # self.backend.closeSection(name, section_id)
        # # Save multiple values given by the iterator in Result.value_iterable
        # elif value is None:
            # if value_iterable is not None:
                # if not repeats:
                    # logger.error("A repeating value was given although the value with metaname '{}' should not repeat.".format(name))
                    # return

                # section_id = self.backend.openSection(name)
                # for value in value_iterable:
                    # print value
                    # # Save to backend
                    # self.input_value_to_backend(name, value, unit, dtypestr, shape)
                # self.backend.closeSection(name, section_id)

    # def input_value_to_backend(self, name, value, unit, dtypestr, shape):
        # """Detects the result type and calls the correct backend function.
        # """
        # # See if the type is correct or can be automatically casted to
        # # the correct type
        # value = self.type_checker(value, dtypestr)

        # # Convert to SI units if unit has been specified
        # if unit is not None:
            # value = convert_unit(value, unit)

        # if len(shape) != 0:
            # self.backend.addArrayValues(name, value)
        # elif dtypestr == "C" or dtypestr == "b":
            # self.backend.addValue(name, value)
        # elif dtypestr == "f" or dtypestr == "i":
            # self.backend.addRealValue(name, value)
        # else:
            # logger.error("Could not determine the backend function call for variable type '{}'".format(type(dtypestr)))

    # def type_checker(self, value, expected_type):
        # """Check that the result can be interpreted as the expected type.
        # """
        # # TODO
        # return value



# #===============================================================================
# class ResultCode(Enum):
    # """Enumeration for indicating the result status.
    # """
    # fail = 0
    # success = 1


# #===============================================================================
# class Result(object):
    # """ Encapsulates a parsing result.

    # The parser should return results as Result objects, which contain
    # additional data for automatic conversion and formatting.

    # The actual value can be single value (string, integer, float, 3D array of
    # floats, 1D array of integer, etc.) or an iterable object for repeatable
    # quantities (those that have "repeats: true" in metaInfo).

    # If returning a non-repeating value, you can place it to the "value" member.
    # Repeatable objects should be placed to the "value_iterable" object.

    # The repeatable values can also be given as generator functions. With
    # generators you can easily push results from a big data file piece by piece
    # to the backend without loading the entire file into memory.

    # Attributes:
        # cache: Boolean indicating whether the result should be cached in memory.
        # name: The name of the metainfo corresponding to this result
        # value: The value of the result. Used for storing single results.
        # value_iterable: Iterable object containing multiple results.
        # unit: Unit of the result. Use the Pint units from UnitRegistry. e.g.
              # unit = ureg.newton. Used to automatically convert to SI.
        # dtypstr: The datatype string specified in metainfo.
        # shape: The expected shape of the result specified in metainfo.
        # repeats: A boolean indicating if this value can repeat. Specified in
                 # metainfo.

    # """

    # def __init__(self):
        # self.name = None
        # self.value = None
        # self.value_iterable = None
        # self.unit = None
        # self.code = ResultCode.success
        # self.error_message = ""
        # self.dtypestr = None
        # self.repeats = None
        # self.shape = None
        # self.cache = False
