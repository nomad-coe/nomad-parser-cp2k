import os
import sys
import logging
import StringIO
from abc import ABCMeta, abstractmethod
from parsercp2k.parsing.outputparsing import *
from nomadcore.simple_parser import SimpleParserBuilder, defaultParseFile, extractOnCloseTriggers
from nomadcore.local_meta_info import loadJsonFile, InfoKindEl
from nomadcore.caching_backend import CachingLevel, ActiveBackend
from nomadcore.simple_parser import mainFunction
logger = logging.getLogger(__name__)


#===============================================================================
class Parser(object):
    """A base class for nomad parsers.

    Attributes:
        self.implementation: an object that actually does the parsing and is
            setup by this class based on the given contents.
    """
    __metaclass__ = ABCMeta
    parser_name = None

    def __init__(self, contents, metainfo_to_keep=None, backend=None):
        """
        Args:
            contents: list of absolute filepaths as strings
            metainfo_to_keep: list of metainfo names to parse as strings.
            backend: the backend where the parsing results are outputted
        """
        self.initialize(contents, metainfo_to_keep, backend)

    def initialize(self, contents, metainfo_to_keep, backend):
        """Initialize the parser with the given environment.
        """
        self.parser_context = ParserContext()
        self.parser_context.backend = backend
        self.parser_context.metainfo_to_keep = metainfo_to_keep
        self.implementation = None

        # If single path provided, make it into a list
        if isinstance(contents, basestring):
            contents = [contents]

        # Figure out all the files from the contents
        if contents:
            files = set()
            for content in contents:
                if os.path.isdir(content):
                    dir_files = set()
                    for filename in os.listdir(content):
                        dir_files.add(os.path.join(content, filename))
                    files |= dir_files
                elif os.path.isfile(content):
                    files.add(content)
                else:
                    logger.error("The string '{}' is not a valid path.".format(content))

            # Filter the files leaving only the parseable ones. Each parser can
            # specify which files are of interest or to include them all.
            self.parser_context.files = self.search_parseable_files(files)

    @abstractmethod
    def setup(self):
        """Deduce the version of the software that was used and setup a correct
        implementation. The implementations should subclass
        ParserImplementation and be stored to the 'implementation' attribute of
        this class. You can give the parser_context wrapper object in the
        parser implementation constructor to pass all the relevant data onto
        the implementation.
        """
        pass

    @abstractmethod
    def search_parseable_files(self, files):
        """From a list of filenames tries to guess which files are relevant to
        the parsing process. Essentially filters the files before they are sent
        to the parser implementation.
        """
        return files

    @abstractmethod
    def get_metainfo_filename(self):
        """This function should return the name of the metainfo file that is
        specific for this parser. This name is used by the Analyzer class in
        the nomadtoolkit.
        """
        return None

    def parse(self):
        """Starts the actual parsing process outputting the results to the
        backend.
        """
        self.setup()
        if not self.implementation:
            logger.error("No parser implementation has been setup.")

        # Write the starting bracket
        self.backend.fileOut.write("[")

        self.implementation.parse()

        # Write the ending bracket
        self.backend.fileOut.write("]\n")

    def scala_main_function(self):
        """This function gets called when the scala calls for a parser.
        """

        # Get the outputparser class
        outputparser = globals()["CP2KOutputParser{}".format("262")](None, None)

        # Setup the metainfos
        metaInfoPath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../nomad-meta-info/meta_info/nomad_meta_info/{}".format(self.get_metainfo_filename())))
        metaInfoEnv, warnings = loadJsonFile(filePath=metaInfoPath, dependencyLoader=None, extraArgsHandling=InfoKindEl.ADD_EXTRA_ARGS, uri=None)

        # Parser info
        parserInfo = {'name': 'cp2k-parser', 'version': '1.0'}

        # Adjust caching of metadata
        cachingLevelForMetaName = outputparser.cachingLevelForMetaName

        # Supercontext is where the objet where the callback functions for
        # section closing are found
        superContext = outputparser

        # Main file description is the SimpleParser tree
        mainFileDescription = outputparser.outputstructure

        # Use the main function from nomadcore
        mainFunction(mainFileDescription, metaInfoEnv, parserInfo, superContext=superContext, cachingLevelForMetaName=cachingLevelForMetaName, onClose={})


#===============================================================================
class ParserImplementation(object):
    """The base class for parsers in the NoMaD project.

    What you can expect from this class:

        - Provides a starting point for the parser developers, but allows
          freedom to do the actual implementation in any way you like.
        - Automation and help with the unit conversion and JSON formatting.
        - Tools for accessing file contents and file handles.
        - Provides the push interface for results.
        - Access to the SimpleParser architecture

    This class defines a few abstract methods that each parser must implement
    (actually raises a compilation error if you don't). This enforces a minimal
    interface that can be expected from each parser, but leaves the
    implementation details to the developer.

    Attributes:
        See the ParserContext class for more details about the attributes.
        _file_handles: A "private" dictionary containing the cached file handles
        _file_contents: A "private" dictionary containing the cached file contents
        _file_sizes: A "private" dictionary containing the cached file sizes
        file_ids: A dictionary containing the mapping between file ids and filepaths
    """

    __metaclass__ = ABCMeta

    def __init__(self, parser_context):

        # Copy all the attributes from the ParserContext object
        attributes = dir(parser_context)
        for attribute in attributes:
            if not attribute.startswith("__"):
                setattr(self, attribute, getattr(parser_context, attribute))

        self._file_handles = {}
        self._file_contents = {}
        self._file_sizes = {}
        self.file_ids = {}

    def setup_given_file_ids(self):
        """Saves the file id's that were given in the JSON input.
        """
        for path, file_id in self.files.iteritems():
            if file_id:
                self.setup_file_id(path, file_id)

    @abstractmethod
    def parse(self):
        """Start the parsing. Will try to parse everything unless given special
        rules (metaInfoToKeep, metaInfoToSkip)."""
        pass

    def parse_file(
            self,
            fileToParse,
            mainFileDescription,
            parserInfo,
            cachingLevelForMetaName={},
            defaultDataCachingLevel=CachingLevel.ForwardAndCache,
            defaultSectionCachingLevel=CachingLevel.Forward,
            superContext=None,
            onClose={}):
        """Uses the SimpleParser utilities to to parse a file.

        Args:
        Returns:
        """

        metainfo_to_keep = self.metainfo_to_keep
        backend = self.backend

        # Initialize the parser builder
        parserBuilder = SimpleParserBuilder(mainFileDescription, backend.metaInfoEnv(), metainfo_to_keep)
        if logger.isEnabledFor(logging.DEBUG):
            s = StringIO.StringIO()
            s.write("matchers:")
            parserBuilder.writeMatchers(s, 2)
            logger.debug(s.getvalue())

        # Verify the metainfo
        if not parserBuilder.verifyMetaInfo(sys.stderr):
            sys.exit(1)

        # Gather onClose functions from supercontext
        if superContext:
            onClose = dict(onClose)
            for attr, callback in extractOnCloseTriggers(superContext).items():
                oldCallbacks = onClose.get(attr, None)
                if oldCallbacks:
                    oldCallbacks.append(callback)
                else:
                    onClose[attr] = [callback]

        # Setup the backend that caches ond handles triggers
        backend = ActiveBackend.activeBackend(
            metaInfoEnv=backend.metaInfoEnv(),
            cachingLevelForMetaName=cachingLevelForMetaName,
            defaultDataCachingLevel=defaultDataCachingLevel,
            defaultSectionCachingLevel=defaultSectionCachingLevel,
            onClose=onClose,
            superBackend=backend)

        # Compile the SimpleMatcher tree
        parserBuilder.compile()
        if logger.isEnabledFor(logging.DEBUG):
            s = StringIO.StringIO()
            s.write("compiledMatchers:")
            parserBuilder.writeCompiledMatchers(s, 2)
            logger.debug(s.getvalue())

        writeComma = False
        outF = sys.stdout
        parse_function = defaultParseFile(parserInfo)
        uri = None
        if uri is None and fileToParse:
            uri = "file://" + fileToParse
        if fileToParse:
            if writeComma:
                outF.write(", ")
            else:
                writeComma = True
            parse_function(parserBuilder, uri, fileToParse, backend, self)

    def setup_file_id(self, path, file_id):
        """Used to map a simple identifier string to a file path. When a file
        id has been setup, you can easily access the file by using the
        functions get_file_handle() or get_file_contents()
        """
        if path in self.files:
            value = self.file_ids.get(file_id)
            if value:
                value.append(path)
            else:
                pathlist = []
                pathlist.append(path)
                self.file_ids[file_id] = pathlist
        else:
            logger.error("Trying to setup an id for an undefined path. See that the path was written correctly and it was given in the files attribute of the JSON string.")

    def get_filepath_by_id(self, file_id, show_warning=True):
        """Get the file paths that were registered with the given id.
        """
        value = self.file_ids.get(file_id)
        if value:
            if isinstance(value, list):
                n = len(value)
                if n == 1:
                    return value[0]
                elif n == 0:
                    if show_warning:
                        logger.warning("No files set with id '{}'".format(file_id))
                    return None
                else:
                    if show_warning:
                        logger.debug("Multiple files set with id '{}'".format(file_id))
                    return value
        else:
            if show_warning:
                logger.warning("No files set with id '{}'".format(file_id))

    def get_file_handle(self, file_id, show_warning=True):
        """Get the handle for a single file with the given id. Uses cached result
        if available. Always seeks to beginning of file before returning it.
        """
        # Get the filepath(s)
        path = self.get_filepath_by_id(file_id, show_warning)
        if not path:
            if show_warning:
                logger.warning("No filepaths registered to id '{}'. Register id's with setup_file_id().".format(file_id))
            return

        if isinstance(path, list):
            if len(path) == 0:
                return
            elif len(path) != 1:
                logger.error("Multiple filepaths found with id '{}'. Use get_file_handles() instead if you expect to have multiple files.".format(file_id))
                return
            else:
                path = path[0]

        # Search for filehandles, if not present create one
        handle = self._file_handles.get(path)
        if not handle:
            try:
                handle = open(path, "r")
            except (OSError, IOError):
                logger.error("Could not open file: '{}'".format(path))
            else:
                self._file_handles[file_id] = handle
        handle.seek(0, os.SEEK_SET)
        return handle

    def get_file_handles(self, file_id, show_warning=True):
        """Get the handles for multiple files with the given id. Uses cached result
        if available. Always seeks to beginning of files before returning them.
        """
        # Get the filepath(s)
        paths = self.get_filepath_by_id(file_id, show_warning)
        if not paths:
            return
        if not isinstance(paths, list):
            paths = [paths]

        # Search for filehandles, if not present create one
        handles = []
        for path in paths:
            handle = self._file_handles.get(path)
            if not handle:
                try:
                    handle = open(path, "r")
                except (OSError, IOError):
                    logger.error("Could not open file: '{}'".format(path))
                else:
                    self._file_handles[file_id] = handle
            handle.seek(0, os.SEEK_SET)
            handles.append(handle)

        # Return handles
        if len(handles) == 0:
            return None
        else:
            return handles

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
class ParserContext(object):
    """Contains everything needed to instantiate a parser implementation.
    """
    def __init__(self, files=None, metainfo_to_keep=None, backend=None, version_id=None):
        self.files = files
        self.version_id = version_id
        self.metainfo_to_keep = metainfo_to_keep
        self.backend = backend
