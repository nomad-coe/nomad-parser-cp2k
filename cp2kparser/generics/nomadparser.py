import json
import os
import logging
import numpy as np
logger = logging.getLogger(__name__)
from abc import ABCMeta, abstractmethod
from enum import Enum
import sys


#===============================================================================
class NomadParser(object):
    """The base class for parsers in the NoMaD project.

    What you can expect from this class:

        - Provides a starting point for the parser developers, but allows
          freedom to do the actual implementation in any way you like.
        - Automation and help with the unit conversion and JSON formatting.
        - Tools for accessing file contents and file handles.
        - Provides the push interface for results.

    This class defines a few abstract methods that each parser must implement
    (actually raises a compilation error if you don't). This enforces a minimal
    interface that can be expected from each parser, but leaves the
    implementation details to the developer.

    To initialize a NomadParser, you need to give it a JSON string in the
    constructor. JSON is used because it is language-agnostic and can easily given
    as a run argument for the parser. An example of the JSON file might look like
    this:

        {
            "metaInfoFile": "/home/metainfo.json"
            "tmpDir": "/home",
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
        - tmpDir: A temporary directory for data
        - metainfoToKeep: What metainfo should be parsed. If empty, tries to
          parse everything except the ones specified in 'metainfoToSkip'
        - metainfoToSkip: A list of metainfos that should be ignored
        - files: Dictionary of files. The key is the path to the file, and the
          value is an optional identifier that can be provided or later
          determined by the parser.

    Attributes:
        input_json_string: A string containing the JSON input.
        input_json_object: The JSON string decoded as an accessible object.
        files: A dictionary of file paths as keys and id's as values. These ids's only include
        the ones given at initialization in the input JSON."
        tmp_dir: Temporary directory location.
        metainfo_file: Path to the file where the metainfos are declared
        meta_info_to_keep:
        meta_info_to_skip:
        file_ids: A dictionary containing all the assigned id's as keys and their
        respective filepaths as values.
        test_mode: A boolean for turning on test mode. In test mode the parsed
        values are not converted to SI or formatted as JSON and they are not
        sent to the backend but returned directly as one possibly large value.
        backend: An object responsible for the JSON formatting and sending the
        results to the scala layer.
    """
    __metaclass__ = ABCMeta

    def __init__(self, input_json_string, stream=sys.stdout, test_mode=False):
        self.input_json_string = input_json_string
        self.input_json_object = None
        self.files = {}
        self.tmp_dir = None
        self.metainfo_file = None
        self.metainfos = {}
        self.metainfo_to_keep = None
        self.metainfo_to_skip = None
        self.file_ids = {}
        self.results = {}
        self.filepaths_wo_id = None
        self.test_mode = test_mode
        self.backend = JsonParseEventsWriterBackend(None, stream)

        self._file_handles = {}
        self._file_contents = {}
        self._file_sizes = {}

        self.analyze_input_json()
        self.setup_given_file_ids()

    def analyze_input_json(self):
        """Analyze the validity of the JSON string given as input.
        """
        # Try to decode the input JSON
        try:
            self.input_json_object = json.loads(self.input_json_string)
        except ValueError as e:
            logger.error("Error in decoding the given JSON input: {}".format(e))

        # See if the needed attributes exist
        self.metainfo_file = self.input_json_object.get("metaInfoFile")
        if self.metainfo_file is None:
            logger.error("No metainfo file path specified.")
        self.tmp_dir = self.input_json_object.get("tmpDir")
        if self.tmp_dir is None:
            logger.error("No temporary folder specified.")
        self.files = self.input_json_object.get("files")
        if self.files is None:
            logger.error("No files specified.")
        self.metainfo_to_keep = self.input_json_object.get("metainfoToKeep")
        self.metainfo_to_skip = self.input_json_object.get("metainfoToSkip")

        # Try to decode the metainfo file
        try:
            fh = open(self.metainfo_file, "r")
            metainfo_object = json.load(fh)
        except ValueError as e:
            logger.error("Error in decoding the metainfo JSON: {}".format(e))
        except IOError as e:
            logger.error("Could not open the metainfo file in path: '{}'".format(self.metainfo_file))
        for metainfo in metainfo_object["metaInfos"]:
            self.metainfos[metainfo["name"]] = metainfo

    def setup_given_file_ids(self):
        """Saves the file id's that were given in the JSON input.
        """
        for path, file_id in self.files.iteritems():
            if file_id:
                self.setup_file_id(path, file_id)

    @abstractmethod
    def setup_version(self):
        """Do some version specific setup work. The parsers will have to
        support many versions of the same code and the results of different
        versions may have to be parsed differently.

        With this function you should determine the version of the software,
        and setup the version specific implementation of the parser.
        """
        pass

    @abstractmethod
    def get_supported_quantities(self):
        """Return a list of the nomad quantities that this parser supports. The
        list should contain the metaInfoNames of the supported quantities.
        """
        pass

    @abstractmethod
    def start_parsing(self, name):
        """Start parsing the given quantity and outputs the result to the
        backend.

        There are two modes of operation:

            automatic: If this function returns a Result object, the function
            parse_quantity will detect it, convert the units, format the
            result to JSON and send it to the backend. Supports also returning
            iterators that yield multiple results (handy for generator
            functions that loop over e.g. a trajectory file extracting the
            trajectory one configuration at a time without reading the entire
            file into memory).

            manual: You use the backend explicitly and do the unit
            conversion and JSON formatting "manually". In this case the
            function should return 'None'.

        """
        pass

    def check_quantity_availability(self, name):
        """Check if the given quantity can be parsed with this parser setup.
        Checks through the list given by get_supported_quantities and also
        checks the metainfoToSkip parameter given in the JSON input.
        """
        if name not in self.get_supported_quantities():
            return False
        if name in self.metainfo_to_skip:
            logger.error("The metaname '{}' cannot be calculated as it is in the list 'metaInfoToSkip'.".format(name))
            return False
        return True

    def parse(self):
        """Start parsing the contents.
        """
        # Determine which values in metainfo are parseable
        metainfos = self.metainfos.itervalues()
        for metainfo in metainfos:
            name = metainfo["name"]
            if self.check_quantity_availability(name):
                self.parse_quantity(name)

    def parse_quantity(self, name):
        """Given a unique quantity id (=metaInfo name) which is supported by
        the parser, parses the corresponding quantity (if available), converts
        it to SI units and return the value as json.
        """

        logger.info("GETTING QUANTITY '{}'".format(name))

        #Check availability
        available = self.check_quantity_availability(name)
        if not available:
            return

        # Get the result by parsing or from cache
        result = self.get_result_object(name)

        if result is not None:
            if isinstance(result, Result):
                if not self.test_mode:
                    metainfo = self.metainfos.get(name)
                    result.name = name
                    result.dtypstr = metainfo.get("dtypeStr")
                    result.repeats = metainfo.get("repeats")
                    result.shape = metainfo.get("shape")
                    self.result_saver(result)
                # In test mode just return the values directly
                else:
                    if result.value is not None:
                        if result.value_iterable is None:
                            return result.value
                    elif result.value_iterable is not None:
                        values = []
                        for value in result.value_iterable:
                            values.append(value)
                        values = np.array(values)
                        if values.size != 0:
                            return values

    def get_result_object(self, name):
        # Check cache
        result = self.results.get(name)
        if result is None:
            result = self.start_parsing(name)
            if result.cache:
                self.results[name] = result
        return result

    def result_saver(self, result):
        """Given a result object, saves the results to the backend.

        The numeric results are automatically converted to SI units if a unit
        has been defined. Automatic conversion to the correct data type
        defined in the metainfo is attempted.
        """
        name = result.name
        value = result.value
        unit = result.unit
        value_iterable = result.value_iterable
        repeats = result.repeats
        dtypestr = result.dtypstr
        shape = result.shape

        # Save a single result
        if value is not None:
            if value_iterable is None:
                if repeats:
                    logger.error("A repeating value was given in Result.value. Repeating values should be stored in Result.value_iterable instead.")
                    return

                # Save to backend
                section_id = self.backend.openSection(name)
                self.input_value_to_backend(name, value, unit, dtypestr, shape)
                self.backend.closeSection(name, section_id)
        # Save multiple values given by the iterator in Result.value_iterable
        elif value is None:
            if value_iterable is not None:
                if not repeats:
                    logger.error("A repeating value was given although the value with metaname '{}' should not repeat.".format(name))
                    return

                section_id = self.backend.openSection(name)
                for value in value_iterable:
                    print value
                    # Save to backend
                    self.input_value_to_backend(name, value, unit, dtypestr, shape)
                self.backend.closeSection(name, section_id)

    def input_value_to_backend(self, name, value, unit, dtypestr, shape):
        """Detects the result type and calls the correct backend function.
        """
        # See if the type is correct or can be automatically casted to
        # the correct type
        value = self.type_checker(value, dtypestr)

        # Convert to SI units if unit has been specified
        if unit is not None:
            value = self.to_SI(value, unit)

        if len(shape) != 0:
            self.backend.addArrayValues(name, value)
        elif dtypestr == "C" or dtypestr == "b":
            self.backend.addValue(name, value)
        elif dtypestr == "f" or dtypestr == "i":
            self.backend.addRealValue(name, value)
        else:
            logger.error("Could not determine the backend function call for variable type '{}'".format(type(dtypestr)))

    def type_checker(self, value, expected_type):
        """Check that the result can be interpreted as the expected type.
        """
        # TODO
        return value

    def to_SI(self, value, unit):
        """If units have been defined to the result, convert the units to SI.
        """
        # Do the conversion to SI units based on the given units and type
        value = value * unit
        converted = value.to_base_units()
        return converted.magnitude

    def setup_file_id(self, path, file_id):
        """Used to map a simple identifier string to a file path. When a file
        id has been setup, you can easily access the file by using the
        functions get_file_handle() or get_file_contents()
        """
        if path in self.files:
            self.file_ids[file_id] = path
        else:
            logger.error("Trying to setup an id for an undefined path. See that the path was written correctly and it was given in the files attribute of the JSON string.")

    def get_file_handle(self, file_id):
        """Get the handle for a file with the given id. Uses cached result
        if available. Always seeks to beginning of file before returning it.
        """
        handle = self._file_handles.get(file_id)
        if not handle:
            path = self.file_ids.get(file_id)
            if not path:
                logger.warning("The file with id '{}' could not be found. You have either not registered this id, or the parser was not given files with this extension.".format(file_id))
                return
            try:
                handle = open(path, "r")
            except (OSError, IOError):
                logger.error("Could not open file: '{}'".format(path))
            else:
                self._file_handles[file_id] = handle
        handle.seek(0, os.SEEK_SET)
        return handle

    def get_file_contents(self, file_id):
        """Get the contents for the file with the given id. Uses cached result
        if available. Does not cache files that are bigger than a certain
        limit.
        """
        cache_limit = 10000
        contents = self._file_contents.get(file_id)
        if not contents:
            fh = self.get_file_handle(file_id)
            fh.seek(0)
            contents = fh.read()
            if self.get_file_size(file_id) <= cache_limit:
                self._file_contents[file_id] = contents
        return contents

    def get_file_size(self, file_id):
        """Get the size of a file with the given id. Uses cached result
        if available.
        """
        size = self._file_sizes.get(file_id)
        if not size:
            fh = self.get_file_handle(file_id)
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            self._file_sizes[file_id] = size
        return size


#===============================================================================
class ResultCode(Enum):
    """Enumeration for indicating the result status.
    """
    fail = 0
    success = 1


#===============================================================================
class Result(object):
    """ Encapsulates a parsing result.

    The parser should return results as Result objects, which contain
    additional data for automatic conversion and formatting.

    The actual value can be single value (string, integer, float, 3D array of
    floats, 1D array of integer, etc.) or an iterable object for repeatable
    quantities (those that have "repeats: true" in metaInfo).

    If returning a non-repeating value, you can place it to the "value" member.
    Repeatable objects should be placed to the "value_iterable" object.

    The repeatable values can also be given as generator functions. With
    generators you can easily push results from a big data file piece by piece
    to the backend without loading the entire file into memory.

    Attributes:
        cache: Boolean indicating whether the result should be cached in memory.
        name: The name of the metainfo corresponding to this result
        value: The value of the result. Used for storing single results.
        value_iterable: Iterable object containing multiple results.
        unit: Unit of the result. Use the Pint units from UnitRegistry. e.g.
              unit = ureg.newton. Used to automatically convert to SI.
        dtypstr: The datatype string specified in metainfo.
        shape: The expected shape of the result specified in metainfo.
        repeats: A boolean indicating if this value can repeat. Specified in
                 metainfo.

    """

    def __init__(self):
        self.name = None
        self.value = None
        self.value_iterable = None
        self.unit = None
        self.code = ResultCode.success
        self.error_message = ""
        self.dtypestr = None
        self.repeats = None
        self.shape = None
        self.cache = False


#===============================================================================
class JsonParseEventsWriterBackend:
    """This class is a duplicate from the python-common repository. Will be
    removed when the python-common is made into a real library.
    """
    # json content is written to fileOut
    def __init__(self, metaInfoEnv, fileOut = sys.stdout):
        self.__metaInfoEnv = metaInfoEnv
        self.fileOut = fileOut
        self.__gIndex = -1
        self.__openSections = set()
        self.__writeComma = False
        self.__lastIndex = {}

    @staticmethod
    def __numpyEncoder(self, o):
        """new default function for json class so that numpy arrays can be encoded"""
        # check if object is a numpy array
        if isinstance(o, np.ndarray):
            # ensure that we have an array with row-major memory order (C like)
            if not o.flags['C_CONTIGUOUS']:
                o = np.ascontiguousarray(o)
            return o.tolist()
        # see default method in python/json/encoder.py
        else:
            raise TypeError(repr(o) + " is not JSON serializable")

    def __jsonOutput(self, dic):
        """method to define format of json output"""
        if self.__writeComma:
            self.fileOut.write(", ")
        else:
            self.__writeComma = True
        json.dump(dic, self.fileOut, indent = 2, separators = (',', ':')) # default = self.__numpyEncoder)

    def startedParsingSession(self, mainFileUri, parserInfo):
        """should be called when the parsing starts, parserInfo should be a valid json dictionary"""
        self.fileOut.write("""{
  "type": "nomad_parse_events_1_0",
  "mainFileUri": """ + json.dumps(mainFileUri) + """,
  "parserInfo": """ + json.dumps(parserInfo, indent = 2, separators = (',', ':')) + """,
  "events": [""")

    def finishedParsingSession(self, mainFileUri, parserInfo):
        """should be called when the parsing finishes"""
        self.fileOut.write("""]
}""")
        self.fileOut.flush()

    def metaInfoEnv(self):
        """the metaInfoEnv this parser was optimized for"""
        return self.__metaInfoEnv

    def openSections(self):
        """returns the sections that are still open
        sections are identified by metaName and their gIndex"""
        return self.__openSections

    def openSectionInfo(self, metaName, gIndex):
        """returns information on an open section (for debugging purposes)"""
        if (metaName,gIndex) in self.__openSections:
            return "section {} gIndex: {}".format(metaName, gIndex)
        else:
            return "*error* closed section {} gIndex: {}".format(metaName, gIndex)

    def openSection(self, metaName):
        """opens a new section and returns its new unique gIndex"""
        newIndex = self.__lastIndex.get(metaName, -1) + 1
        self.openSectionWithGIndex(metaName, newIndex)
        return newIndex

    def openSectionWithGIndex(self, metaName, gIndex):
        """opens a new section where gIndex is generated externally
        gIndex should be unique (no reopening of a closed section)"""
        self.__lastIndex[metaName] = gIndex
        self.__openSections.add((metaName, gIndex))
        self.__jsonOutput({"event":"openSection", "metaName":metaName, "gIndex":gIndex})

    def setSectionInfo(self, metaName, gIndex, references):
        """sets info values of an open section
        references should be a dictionary with the gIndexes of the root sections this section refers to"""
        self.__jsonOutput({"event":"setSectionInfo", "metaName":metaName, "gIndex":gIndex, "references":references})

    def closeSection(self, metaName, gIndex):
        """closes a section
        after this no other value can be added to the section
        metaName is the name of the meta info, gIndex the index of the section"""
        if (metaName, gIndex) in self.__openSections:
            self.__openSections.remove((metaName, gIndex))
            self.__jsonOutput({"event":"closeSection", "metaName":metaName, "gIndex":gIndex})
        # raise exeption if section is not open
        else:
            raise Exception("There is no open section with metaName %s and gIndex %d" % (metaName, gIndex))

    def addValue(self, metaName, value, gIndex = -1):
        """adds a json value corresponding to metaName
        the value is added to the section the meta info metaName is in
        a gIndex of -1 means the latest section"""
        self.__jsonOutput({"event":"addValue", "metaName":metaName, "gIndex":gIndex, "value":value})

    def addRealValue(self, metaName, value, gIndex = -1):
        """adds a floating point value corresponding to metaName
        The value is added to the section the meta info metaName is in
        A gIndex of -1 means the latest section"""
        self.__jsonOutput({"event":"addRealValue", "metaName":metaName, "gIndex":gIndex, "value":value})

    def addArray(self, metaName, shape, gIndex = -1):
        """adds a new array value of the given size corresponding to metaName
        the value is added to the section the meta info metaName is in
        a gIndex of -1 means the latest section
        the array is unitialized"""
        self.__jsonOutput({"event":"addArray", "metaName":metaName, "gIndex":gIndex, "shape":shape})

    def setArrayValues(self, metaName, values, offset = None, gIndex = -1):
        """adds values to the last array added, array must be a numpy array"""
        res = {
            "event":"setArrayValues",
            "metaName":metaName,
            "gIndex":gIndex,
            "valuesShape":values.shape,
            "flatValues": values.flatten().tolist()
        }
        if offset:
            res["offset"] = offset
        self.__jsonOutput(res)

    def addArrayValues(self, metaName, values, gIndex = -1):
        """adds an array value with the given array values.
        values must be a numpy array"""
        res = {
            "event":"addArrayValues",
            "metaName":metaName,
            "gIndex":gIndex,
            "valuesShape":values.shape,
            "flatValues": values.flatten().tolist()
        }
        self.__jsonOutput(res)
