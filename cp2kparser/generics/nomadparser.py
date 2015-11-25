import json
import os
import time
from abc import ABCMeta, abstractmethod
import logging
logger = logging.getLogger(__name__)
from cp2kparser import ureg
from enum import Enum


#===============================================================================
class NomadParser(object):
    """The base class for a NoMaD parser.

    This class should be inherited by the python based parsers. It provides
    general utility methods and a single interface for input and output.

    The utilities that this class provides and the inherited classes should NOT
    do:
        - Converting results to JSON
        - Converting units to SI
        - Timing
        - Caching of results
        - Providing file contents, sizes and handles

    This class also defines some absract methods that each parser must
    implement.
    """
    __metaclass__ = ABCMeta

    def __init__(self, input_json_string):
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

    def get_file_contents(self, file_id):
        """Get the contents for the file with the given id. Uses cached result
        if available. Does not cache files that are bigger than a certain
        limit.
        """
        cache_limit = 10000
        contents = self.file_contents.get(file_id)
        if not contents:
            fh = self.file_handles[file_id]
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

    def get_file_handle(self, file_id):
        """Get the handle for a file with the given id. Uses cached result
        if available. Always seeks to beginning of file before returning it.
        """
        handle = self.file_handles.get(file_id)
        if not handle:
            path = self.file_ids.get(file_id)
            if not path:
                logger.warning("The file with id '{}' could not be found. Probable reason for this is that the parser was not given files with this extension.")
                return
            try:
                handle = open(path, "r")
            except (OSError, IOError):
                logger.error("Could not open file: '{}'".format(path))
            else:
                self.file_handles[file_id] = handle
        handle.seek(0, os.SEEK_SET)
        return handle

    def analyse_input_json(self):
        """Analyze the JSON given as input.
        """
        # Try to decode
        self.input_json_object = json.loads(self.input_json_string)

        # See if the needed attributes exist
        self.tmp_dir = self.input_json_object.get("tmpDir")
        if self.tmp_dir is None:
            logger.error("No temporary folder specified.")
        self.files = self.input_json_object.get("files")
        if self.files is None:
            logger.error("No files specified.")
        self.metainfo_to_keep = self.input_json_object.get("metainfoToKeep")
        self.metainfo_to_skip = self.input_json_object.get("metainfoToSkip")

        # See if the metainfos exist

    def get_quantity(self, name):
        """Given a unique quantity id which is present in the metainfo
        declaration, parses the corresponding quantity (if available), converts
        it to SI units and return the value as json.
        """
        # Start timing
        logger.info("===========================================================================")
        logger.info("GETTING QUANTITY '{}'".format(name))
        start = time.clock()

        #Check availability
        available = self.check_quantity_availability(name)
        if not available:
            logger.warning("The quantity '{}' is not available for this parser version.".format(name))
            return

        # Check cache
        result = self.results.get(name)
        if not result:
            # Ask the engine for the quantity
            result = self.get_quantity_json(name)
            self.results[name] = result
        else:
            logger.debug("Using cached result.")
        if result is None:
            logger.debug("The quantity '{}' is not present or could not be succesfully parsed.".format(name))

        # Check results
        if result is None:
            logger.info("There was an issue in parsing quantity '{}'. It is either not present in the files or could not be succesfully parsed.".format(name))
        else:
            logger.info("Succesfully parsed quantity '{}'.".format(name))

        stop = time.clock()
        logger.info("Elapsed time: {} ms".format((stop-start)*1000))
        logger.info("Result: {}".format(result))
        logger.info("")

        return result

    def get_quantity_json(self, name):
        result_si = self.get_quantity_SI(name)
        return result_si

    def get_quantity_SI(self, name):
        result = self.get_quantity_unformatted(name)

        # Do the conversion to SI units based on the given units
        converted_result = result.value
        if result.unit is not None:
            converted_result = self.convert_units(result)

        return converted_result

    def get_all_quantities(self):
        """Parse all supported quantities."""
        implementation_methods = [method for method in dir(self.implementation) if callable(getattr(self.implementation, method))]
        for method in implementation_methods:
            if method.startswith("_Q_"):
                method = method[3:]
                self.get_quantity(method)

    def convert_units(self, result):
        """Provided floating point data as the input, this function will perform
        a conversion to SI units from the specified units. The conversion could
        be done by the subclass but then maintaining the conversion would
        become much more difficult.

        Supports single floating point numbers, arbitrary dimensional numpy
        arrays and regular lists/tuples of floating point numbers.
        """
        return_type = result.return_type
        value = result.value * result.unit

        # Energy to joule
        if return_type == Result.energy:
            converted = value.to(ureg.joule)

        # Force to newton
        if return_type == Result.force:
            converted = value.to(ureg.newton)

        return converted

    def jsonify(self, data):
        """ Formats the result as a json string.
        """
        pass

    @abstractmethod
    def setup_version(self):
        """Setup a correct implementation for this version.
        """
        pass

    @abstractmethod
    def determine_file_ids(self):
        """If the files have not been given an id, try to determine the
        correct ids by looking at the input file, contents and file extensions.
        """
        pass

    @abstractmethod
    def get_quantity_unformatted(self, name):
        """Parse a quantity from the given files. Should return a tuple
        containing the result object (numeric results preferably as numpy
        arrays) and the unit of the result (None if no unit is needed)
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


#===============================================================================
class ResultCode(Enum):
    """Enumeration for indicating the result status.
    """
    fail = 0
    success = 1


#===============================================================================
class ResultKind(Enum):
    """Enumeration for indicating the type of returned value.
    """
    energy = "energy"
    force = "force"
    text = "text"
    number = "number"


#===============================================================================
class Result(object):
    """ Encapsulates a parsing result.
    """

    def __init__(self, value=None, kind=None, unit=None, code=ResultCode.success):
        self.value = value
        self.unit = unit
        self.kind = kind
        self.code = code
        self.error_message = ""
