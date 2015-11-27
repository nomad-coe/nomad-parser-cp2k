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

    This class provides general utility methods and a uniform interface for
    input and output. :
        - Provides a starting point for the parser developers, but allows
          freedom to do the actual implementation in any way you like.
        - Automation and help with the unit conversion and JSON formatting.
        - Tools for accessing file contents and file handles.
        - Provides the push interface for results.

    This class defines a few abstract methods that each parser must implement
    (actually raises a compilation error if you dont). This enforces a minimal
    interface that can be expected from each parser, but leaves the
    implementation details to the developer.

    To initialize a NomadParser, you need to give it a JSON string in the
    constructor. JSON is used because it is language-agnostic and can easily given
    as a run argument for the parser. An example of the JSON file might look like
    this:

        {
            "tmpDir": "/home/lauri",
            "metainfoToKeep": ["energy"],
            "metainfoToSkip": ["particle_forces"],
            "files": {
                "/home/output.out": "output",
                "/home/input.inp": "input",
                "/home/coords.xyz": ""
            }
        }

    Here is an explanation of the different attributes:
        - tmpDir: A temporary directory for data
        - metainfoToKeep: What metainfo should be parsed. If empty, tries to
          parse everything except the ones specified in 'metainfoToSkip'
        - metainfoToSkip: A list of metainfos that should be ignored
        - files: Dictionary of files. The key is the path to the file, and the
          value is an optional identifier that can be provided or later
          determined by the parser.

    When you make a subclass of this class, you should remember to call the
    constructor of the base class. Example:

        class MyParser(NomadParser):

            def __init__(self, input_json_string, stream=sys.stdout, test=False):

    """
    __metaclass__ = ABCMeta

    def __init__(self, input_json_string, stream=sys.stdout, test=False):
        self.input_json_string = input_json_string
        self.input_json_object = None
        self.files = {}
        self.tmp_dir = None
        self.metainfo_to_keep = None
        self.metainfo_to_skip = None
        self.file_ids = {}
        self.file_handles = {}
        self.interface_object = None
        self.implementation = None
        self.file_contents = {}
        self.file_sizes = {}
        self.results = {}
        self.test = test
        self.backend = JsonParseEventsWriterBackend(None, stream)
        self.analyze_input_json()
        self.setup_given_file_ids()

    def analyze_input_json(self):
        """Analyze the validity of the JSON string given as input.
        """
        # Try to decode
        try:
            self.input_json_object = json.loads(self.input_json_string)
        except ValueError as e:
            logger.error("Error in decoding the given JSON input: {}".format(e))

        # See if the needed attributes exist
        self.tmp_dir = self.input_json_object.get("tmpDir")
        if self.tmp_dir is None:
            logger.error("No temporary folder specified.")
        self.files = self.input_json_object.get("files")
        if self.files is None:
            logger.error("No files specified.")
        self.metainfo_to_keep = self.input_json_object.get("metainfoToKeep")
        self.metainfo_to_skip = self.input_json_object.get("metainfoToSkip")

    @abstractmethod
    def determine_file_ids_pre_setup(self):
        """If the files have not been given an id, try to determine the
        correct ids by looking at the input file, contents and file extensions.

        You dont have to assign an ID to the files, but it can make your life
        much easier. If you have assigned an ID to a file, you automatically
        get access to these functions:

            - get_file_handle(id): Returns a python file object that has been
              reset to the beginning of file.
            - get_file_contents(id): Returns the contents of a file as a
              string. If the file is considered small, returns a the contents
              from cache.
        """
        pass

    @abstractmethod
    def setup_version(self):
        """Do some version specific setup work. The parsers will have to
        support many versions of the same code and the results of different
        versions may have to be parsed differently.

        Here you can determine the version of the software, and setup the
        version specific implementation of the parser.
        """
        pass

    @abstractmethod
    def determine_file_ids_post_setup(self):
        """
        """
        pass

    @abstractmethod
    def check_quantity_availability(self, name):
        """Check quantity availability.
          -Check the list of available quantities declared in interface.
          -Check if the run type actually produces the quantity
          -Check if the quantity is allowed by the 'metainfoToKeep' and
          'metainfoToSkip'
        """
        pass

    @abstractmethod
    def start_parsing(self, name):
        """Start parsing the given quantity and output the result to the
        backend.

        There are two modes of operation:

            manual: This function uses the backend explicitly and does to unit
            conversion and JSON formatting "manually". In this case the
            function should return 'None'

            automatic: If this function returns a value, the function
            parse_quantity will detect it, convert the units, format the
            result to JSON and send it to the backend. Supports also generators.
        """
        pass

    def parse_quantity(self, name):
        """Given a unique quantity id which is present in the metainfo
        declaration, parses the corresponding quantity (if available), converts
        it to SI units and return the value as json.
        """
        # Start timing
        logger.info("===========================================================================")
        logger.info("GETTING QUANTITY '{}'".format(name))

        #Check availability
        available = self.check_quantity_availability(name)
        if not available:
            logger.warning("The quantity '{}' is not available for this parser version.".format(name))
            return

        result = self.start_parsing(name)
        if result:
            if not self.test:
                # Single Result object
                if isinstance(result, Result):

                    # Determine the type
                    si_result = self.to_SI(result)
                    section_id = self.backend.openSection(name)
                    self.input_result(name, si_result)
                    self.backend.closeSection(name, section_id)
                # Assumes the result to be a generator function which returns
                # multiple Result objects and loops over them
                else:
                    section_id = self.backend.openSection(name)
                    for value in result:
                        si_result = self.to_SI(value)
                        self.input_result(name, si_result)
                        self.backend.addValue(name, si_result)
                    self.backend.closeSection(name, section_id)
            # In test mode return the results as one object and without
            # formatting. Makes writing tests much easier
            else:
                if isinstance(result, Result):
                    return result
                else:
                    results = []
                    for value in result:
                        results.append(value)
                    return np.array(results)

    def input_result(self, name, result):
        if isinstance(result, (float, int)):
            self.backend.addRealValue(name, result)
        elif isinstance(result, np.ndarray):
            self.backend.addArrayValues(name, result)
        elif isinstance(result, (str, unicode)):
            self.backend.addValue(name, result)
        else:
            logger.error("Could not determine the backend function call for variable type '{}'".format(type(result)))

    def to_SI(self, result):
        """If units have been defined to the result, convert the units to SI.
        Does nothing for example to strings or numbers without defined
        units.
        """
        if result.unit is None:
            return result.value

        # Do the conversion to SI units based on the given units and type
        value = result.value * result.unit
        return value.to_base_units().magnitude

    def setup_given_file_ids(self):
        """Saves the file id's that were given in the JSON input.
        """
        resolved = {}
        resolvable = []
        for path, file_id in self.files.iteritems():
            if not file_id:
                resolvable.append(path)
            else:
                resolved[file_id] = path

        for id, path in resolved.iteritems():
            print id
            print path
            self.setup_file_id(path, id)

        self.resolvable = resolvable

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
        handle = self.file_handles.get(file_id)
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
                self.file_handles[file_id] = handle
        handle.seek(0, os.SEEK_SET)
        return handle

    def get_file_contents(self, file_id):
        """Get the contents for the file with the given id. Uses cached result
        if available. Does not cache files that are bigger than a certain
        limit.
        """
        cache_limit = 10000
        contents = self.file_contents.get(file_id)
        if not contents:
            fh = self.get_file_handle(file_id)
            fh.seek(0)
            contents = fh.read()
            if self.get_file_size(file_id) <= cache_limit:
                self.file_contents[file_id] = contents
        return contents

    def get_file_size(self, file_id):
        """Get the size of a file with the given id. Uses cached result
        if available.
        """
        size = self.file_sizes.get(file_id)
        if not size:
            fh = self.file_handles[file_id]
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            self.file_sizes[file_id] = size
        return size

    def get_all_quantities(self):
        """Parse all supported quantities."""
        implementation_methods = [method for method in dir(self.implementation) if callable(getattr(self.implementation, method))]
        for method in implementation_methods:
            if method.startswith("_Q_"):
                method = method[3:]
                self.get_quantity(method)


#===============================================================================
class ResultCode(Enum):
    """Enumeration for indicating the result status.
    """
    fail = 0
    success = 1


#===============================================================================
class Result(object):
    """ Encapsulates a parsing result.
    """

    def __init__(self, value=None, unit=None, code=ResultCode.success):
        self.value = value
        self.unit = unit
        self.code = code
        self.error_message = ""


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
