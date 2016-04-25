"""
This module contains the base classes that help in building parsers for the
NoMaD project.
"""

import os
import logging
from abc import ABCMeta, abstractmethod
from nomadcore.unit_conversion import unit_conversion
from nomadcore.simple_parser import AncillaryParser, mainFunction
from nomadcore.local_backend import LocalBackend
from nomadcore.local_meta_info import load_metainfo
from nomadcore.caching_backend import CachingLevel
logger = logging.getLogger(__name__)


#===============================================================================
class ParserInterface(object):
    """This class provides the interface parsing. The end-user will typically
    only interact with this class. All the input is given to this class (or
    typically a subclass) and the parsing is done by calling the parse()
    method. The parsing output is determined by the backend object that is
    given in the constructor as a dependency.

    Attributes:
        main_parser: Object that actually does the parsing and is
            setup by this class based on the given contents.
        parser_context: A wrapper class for all the parser related information.
            This is contructed here and then passed onto the different
            subparsers.
    """
    __metaclass__ = ABCMeta

    def __init__(self, main_file, metainfo_to_keep=None, backend=None, default_units=None, metainfo_units=None):
        """
    Args:
        main_file: A special file that can be considered the main file of the
            calculation.
        metainfo_to_keep: A list of metainfo names. This list is used to
            optimize the parsing process as optimally only the information
            relevant to these metainfos will be parsed.
        backend: An object to which the parser will give all the parsed data.
            The backend will then determine where and when to output that data.
        """
        self.initialize(main_file, metainfo_to_keep, backend, default_units, metainfo_units)

    def initialize(self, main_file, metainfo_to_keep, backend, default_units, metainfo_units):
        """Initialize the parser with the given environment.
        """
        self.parser_context = ParserContext()
        self.parser_context.metainfo_to_keep = metainfo_to_keep
        self.parser_context.main_file = main_file
        self.parser_context.file_service = FileService()
        self.parser_context.parser_info = self.get_parser_info()
        self.main_parser = None

        # Check that the main file exists
        if not os.path.isfile(main_file):
            logger.error("Couldn't find the main file {}. Check that the path is valid and the file exists on this path.".format(main_file))

        # Load metainfo environment
        metainfo_env, warn = load_metainfo(self.get_metainfo_filename())
        self.parser_context.metainfo_env = metainfo_env

        # Initialize the backend. Use local backend if none given
        if backend is not None:
            self.parser_context.super_backend = backend(metainfo_env)
        else:
            self.parser_context.super_backend = LocalBackend(metainfo_env)

        # Check the list of default units
        default_unit_map = {}
        if default_units is not None:
            for unit in default_units:
                dimension = unit_conversion.ureg(unit).dimensionality
                old_value = default_unit_map.get(str(dimension))
                if old_value is not None:
                    raise LookupError("You can only specify one default value per dimension in the 'default_units' list. There are two different units given for the dimension '{}'".format(dimension))
                default_unit_map[str(dimension)] = unit

        # Check the list of metainfo units
        if metainfo_units is not None:
            for metaname, unit in metainfo_units.iteritems():

                # Check that the unit is OK
                unit_conversion.ureg(unit)

                # Check that the metaname is OK
                meta = metainfo_env.infoKinds.get(metaname)
                if meta is None:
                    raise KeyError("The metainfo name '{}' could not be found. Check for typos or try updating the metainfo repository.".format(metaname))

        # Save the default units
        self.parser_context.default_units = default_unit_map
        self.parser_context.metainfo_units = metainfo_units

    @abstractmethod
    def setup_version(self):
        """Deduce the version of the software that was used and setup a correct
        main parser. The main parser should subclass MainParser and be stored
        to the 'main_parser' attribute of this class. You can give the
        'parser_context' wrapper object in the main parser constructor to pass
        all the relevant data for it.
        """
        pass

    @abstractmethod
    def get_metainfo_filename(self):
        """This function should return the name of the metainfo file that is
        specific for this parser. When the parser is started, the metainfo
        environment is loaded from this file that is located within a separate
        repository (nomad-meta-info).

        Returns:
            A string containing the metainfo filename for this parser.
        """
        return None

    @abstractmethod
    def get_parser_info(self):
        """This function should return a dictionary containing the parser info.
        This info is printed to the JSON backend. it should be of the form:

            {'name': 'softwarename-parser', 'version': '1.0'}

        Returns:
            A dictionary containing information about this parser.
        """
        return None

    def parse(self):
        """Starts the actual parsing process, and outputs the results to the
        backend specified in the constructor.
        """
        self.setup_version()
        if not self.main_parser:
            logger.error("The main parser has not been set up.")

        self.main_parser.parse()

        # If using a local backend, the results will have been saved to a
        # separate results dictionary which should be returned.
        try:
            return self.parser_context.super_backend.results
        except AttributeError:
            return None


#===============================================================================
class FileService(object):
    """Provides the interface to accessing files related to a calculation.

    Before you can use the service you must setup the root path, where every
    file related to this calculation resides. All queries filepaths will be
    handled as relative to this root folder.

    You can also setup ids that point to a certain path. This helps in querying
    the files as you don't have to remember the exact path and you can store
    paths for later use.

    Used to map file paths to certain ID's. This helps in setting up the
    Secondary parsers as you can associate file paths to simpler ID's that are
    easier to use.

    Attributes:
        root_folder: A path to the root folder
        _file_ids: A dictionary containing the mapping between file ids and filepaths
        _file_handles: A "private" dictionary containing the cached file handles
        _file_contents: A "private" dictionary containing the cached file contents
        _file_sizes: A "private" dictionary containing the cached file sizes
    """
    def __init__(self, root_folder=None):
        """
        Args:
            root_folder: a path to the root folder as a string.
        """
        self.map_id_to_path = {}
        if root_folder is not None:
            self.setup_root_folder(root_folder)

    def setup_root_folder(self, root_folder):
        """Setup the path to the root folder. Every filepath you set or get
        through this service should be relative to this root folder.
        """
        if os.path.isdir(root_folder):
            self.root_folder = root_folder
        else:
            raise IOError("Could not find the folder '{}'".format(root_folder))

    def get_absolute_path_to_file(self, relative_path):
        """
        Returns:
            If the given . Return none if no file with the given path can
            be found.
        """
        path = os.path.join(self.root_folder, relative_path)
        if os.path.isfile(path):
            return path
        else:
            logger.error("Could not open the file '{}'.".format(path))
            return None

    def get_file_by_id(self, file_id):
        """
        Returns:
            Handle to the file. Return none if no file with the given id has
            been set.
        """
        path = self.map_id_to_path.get(file_id)
        if path is None:
            logger.error("The id '{}' has no path associated with it.".format(file_id))
            return None
        else:
            return self.get_file_by_path(path)

    def set_file_id(self, path, file_id):
        """Used to map a simple identifier string to a file path. When a file
        id has been setup, you can easily access the file by using the
        functions get_file_handle() or get_file_contents()
        """
        # Check if there is an old definition
        old = self.map_id_to_path.get(file_id)
        if old is not None:
            raise LookupError("The path '{}' is already associated with id '{}'".format(old, file_id))

        # Check that the file exists
        path = os.path.join(self.root_folder, path)
        if not os.path.isfile(path):
            logger.error("Could not set the id for file '{}' as it cannot be found.".format(path))
        else:
            self.map_id_to_path[file_id] = path


#===============================================================================
class BasicParser(object):
    """A base class for all parsers.

    Attributes:
        file_path: Path to a file that is parsed by this class.
        parser_context: The ParserContext object that contains various in-depth
            information about the parsing environment.
        backend: The backend that will cache things according to the rules
            given in the main parser.
        super_backend: The final backend where things are Forwarded to by the
            caching backend.
    """
    __metaclass__ = ABCMeta

    def __init__(self, file_path, parser_context):
        self.file_path = file_path
        self.parser_context = parser_context
        self.backend = parser_context.caching_backend
        self.super_backend = parser_context.super_backend

    @abstractmethod
    def parse(self):
        """Used to do the actual parsing. Inside this function you should push
        the parsing results into the Caching backend, or directly to the
        superBackend. You will also have to open new sections, but remember
        that certain sections may already be opened by other parsers.
        """
        pass


#===============================================================================
class HierarchicalParser(BasicParser):
    """A base class for all parsers that parse a file using a hierarchy of
    SimpleMatcher objects.

    Attributes:
        root_matcher: The SimpleMatcher object at the root of this parser.
            caching_level_for_metaname: A dicionary containing the caching options
            that the ActiveBackend will use for individual metanames.

            Example:
                self.caching_level_for_metaname = {
                    'section_XC_functionals': CachingLevel.ForwardAndCache,
                }
        default_data_caching_level: A default caching level for data, i.e.
            metainfo with kindStr=type_document_content or type_dimension
        default_section_caching_level: A default caching level for sections.
    """
    def __init__(self, file_path, parser_context):
        super(HierarchicalParser, self).__init__(file_path, parser_context)
        self.root_matcher = None
        self.caching_level_for_metaname = {}
        self.default_data_caching_level = CachingLevel.ForwardAndCache
        self.default_section_caching_level = CachingLevel.Forward


#===============================================================================
class SecondaryParser(HierarchicalParser):
    """A base class for ancillary file parsers. Instantiated and run by a
    MainParser.

    Attributes:
        ancillary_parser: An AncillaryParser object
    """
    def __init__(self, file_path, parser_context, simple_parser):
        """
        Args:
            file_path: The path of the file to parse. Can be absolute or relative path.
            simple_parser: The SimpleParser object that is does the actual
                parsing. Shared by the SecondaryParsers and the MainParser.
        """
        super(SecondaryParser, self).__init__(file_path, parser_context)
        self.simple_parser = simple_parser
        self.ancillary_parser = None

    def parse(self):
        """Parser the given ancillary file in place.
        """
        self.ancillary_parser = AncillaryParser(self.root_matcher, self.simple_parser, self.caching_levels, self)

        # Try opening the given file
        try:
            with open(self.file_path) as fIn:
                self.ancillary_parser.parseFile(fIn)
        except IOError:
            dir_name, file_name = os.path.split(os.path.abspath(self.file_path))
            logger.warning("Could not find file '{}' in directory '{}'. No data will be parsed from this file".format(dir_name, file_name))


#===============================================================================
class MainParser(HierarchicalParser):
    """Base class for parsers that parse the main file of a calculation using
    SimpleMatchers. There should only be one main parser, and all other parsers
    are instantiated by this one.
    """

    def __init__(self, file_path, parser_context):
        """
        Args:
            file_path: Path to the main file as a string.
            parser_context: The ParserContext object that contains various
                in-depth information about the parsing environment.
        """
        super(MainParser, self).__init__(file_path, parser_context)
        self.simple_parser = None

    def parse(self):
        """Starts the parsing. By default uses the SimpleParser scheme, if you
        want to use something else or customize the process just override this
        method
        """
        mainFunction(
                mainFileDescription=self.root_matcher,
                metaInfoEnv=self.parser_context.metainfo_env,
                parserInfo=self.parser_context.parser_info,
                outF=self.parser_context.super_backend.fileOut,
                cachingLevelForMetaName=self.caching_level_for_metaname,
                superContext=self,
                onClose={},
                default_units=self.parser_context.default_units,
                metainfo_units=self.parser_context.metainfo_units,
                superBackend=self.parser_context.super_backend,
                mainFile=self.parser_context.main_file)

    def startedParsing(self, fInName, parser):
        """Function is called when the parsing starts.

        Get compiled parser.
        Later one can compile a parser for parsing an external file.
        """
        self.parser_context.caching_backend = parser.backend


#===============================================================================
class ParserContext(object):
    """A container class for storing and moving information about the parsing
    environment. A single ParserContext object is initialized by the Parser
    class, or it's subclass.
    """
    def __init__(self):
        self.main_file = None
        self.version_id = None
        self.metainfo_to_keep = None
        self.super_backend = None
        self.caching_backend = None
        self.default_units = None
        self.metainfo_units = None
        self.file_service = None
        self.metainfo_env = None
        self.parser_info = None


#===============================================================================
# class ParserImplementation(object):
    # """The base class for a version specific parser implementation in. Provides
    # some useful tools for setting up file access.

    # Attributes:
        # parser_context: ParserContext object
        # file_storage: FileStorage object
        # main_parser: MainParser object
    # """
    # def __init__(self, parser_context):

        # self.parser_context = parser_context
        # self.file_storage = FileStorage()
        # self.main_parser = None

        # # Copy all the attributes from the ParserContext object for quick access
        # attributes = dir(parser_context)
        # for attribute in attributes:
            # if not attribute.startswith("__"):
                # setattr(self, attribute, getattr(parser_context, attribute))

        # # self.file_parsers = []

    # # def setup_given_file_ids(self):
        # # """Saves the file id's that were given in the JSON input.
        # # """
        # # for path, file_id in self.files.iteritems():
            # # if file_id:
                # # self.file_storage.setup_file_id(path, file_id)

    # def parse(self):
        # """Start the parsing. Will try to parse everything unless given special
        # rules (metaInfoToKeep)."""
        # self.main_parser.parse()
        # for file_parser in self.file_parsers:
            # file_parser.parse()



        # Initialize the parser builder
        # default_units = self.parser_context.default_units
        # metainfo_units = self.parser_context.metainfo_units
        # parserBuilder = SimpleParserBuilder(self.root_matcher, self.backend.metaInfoEnv(), self.metainfo_to_keep, default_units=default_units, metainfo_units=metainfo_units)

        # # Verify the metainfo
        # if not parserBuilder.verifyMetaInfo(sys.stderr):
            # sys.exit(1)

        # # Gather onClose functions from supercontext
        # onClose = dict(self.onClose)
        # for attr, callback in extractOnCloseTriggers(self).items():
            # oldCallbacks = onClose.get(attr, None)
            # if oldCallbacks:
                # oldCallbacks.append(callback)
            # else:
                # onClose[attr] = [callback]

        # # Setup the backend that caches ond handles triggers
        # self.caching_backend = ActiveBackend.activeBackend(
            # metaInfoEnv=self.backend.metaInfoEnv(),
            # cachingLevelForMetaName=self.caching_level_for_metaname,
            # defaultDataCachingLevel=self.default_data_caching_level,
            # defaultSectionCachingLevel=self.default_section_caching_level,
            # onClose=onClose,
            # superBackend=self.backend,
            # default_units=default_units,
            # metainfo_units=metainfo_units)

        # # Compile the SimpleMatcher tree
        # parserBuilder.compile()

        # self.backend.fileOut.write("[")
        # uri = "file://" + self.file_path
        # parserInfo = {'name': 'cp2k-parser', 'version': '1.0'}
        # self.caching_backend.startedParsingSession(uri, parserInfo)
        # with open(self.file_path, "r") as fIn:
            # parser = parserBuilder.buildParser(PushbackLineFile(fIn), self.caching_backend, superContext=self)
            # parser.parse()
        # self.caching_backend.finishedParsingSession("ParseSuccess", None)
        # self.backend.fileOut.write("]\n")
    # def add_file_id(self, path, file_id):
        # """
        # """
        # value = self.file_ids.get(file_id)
        # if value:
            # if isinstance(value, list):
                # value.append(path)
            # else:
                # raise LookupError("You have already setup an unique file_path '{}' to this id.".format(value))
        # else:
            # pathlist = []
            # pathlist.append(path)
            # self.file_ids[file_id] = pathlist

    # def get_filepath_by_id(self, file_id, show_warning=True):
        # """Get the file paths that were registered with the given id.
        # """
        # value = self.file_ids.get(file_id)
        # if value:
            # if isinstance(value, list):
                # n = len(value)
                # if n == 0:
                    # if show_warning:
                        # logger.warning("No files set with id '{}'".format(file_id))
                    # return None
                # else:
                    # if show_warning:
                        # logger.debug("Multiple files set with id '{}'".format(file_id))
                    # return value
            # else:
                # return value
        # else:
            # if show_warning:
                # logger.warning("No files set with id '{}'".format(file_id))

    # def get_file_handle(self, file_id, show_warning=True):
        # """Get the handle for a single file with the given id. Uses cached result
        # if available. Always seeks to beginning of file before returning it.
        # """
        # # Get the filepath(s)
        # path = self.get_filepath_by_id(file_id, show_warning)
        # if not path:
            # if show_warning:
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

    # def get_file_handles(self, file_id, show_warning=True):
        # """Get the handles for multiple files with the given id. Uses cached result
        # if available. Always seeks to beginning of files before returning them.
        # """
        # # Get the filepath(s)
        # paths = self.get_filepath_by_id(file_id, show_warning)
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
