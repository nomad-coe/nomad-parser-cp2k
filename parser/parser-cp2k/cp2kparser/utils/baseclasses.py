import os
import sys
import logging
from abc import ABCMeta, abstractmethod
from nomadcore.simple_parser import SimpleParserBuilder, extractOnCloseTriggers, PushbackLineFile
from nomadcore.caching_backend import CachingLevel, ActiveBackend
logger = logging.getLogger(__name__)


#===============================================================================
class Parser(object):
    """This class provides the interface for parsing. All the input is given to
    this class (or typically a subclass) and the parsing is done by calling the
    parse() method. The parsing output is determined by the backend object that
    is given in the constructor as a dependency.

    Attributes:
        implementation: an object that actually does the parsing and is
            setup by this class based on the given contents.
        parser_context: A wrapper class for all the parser related information.
            This is contructed here and then passed onto the different
            implementations and FileParsers.
    """
    __metaclass__ = ABCMeta

    def __init__(self, contents, metainfo_to_keep=None, backend=None, main_file=None):
        """
    Args:
        contents: The contents to parse as a list of file and directory paths.
            The given directory paths will be searched recursively for interesting
            files.
        metainfo_to_keep: A list of metainfo names. This list is used to
            optimize the parsing process as optimally only the information relevant
            to these metainfos will be parsed.
        backend: An object to which the parser will give all the parsed data.
            The backend will then determine where and when to output that data.
        main_file: A special file that can be considered the main file.
            Currently used in when interfacing to the scala environment in the
            nomad project.
        """
        self.initialize(contents, metainfo_to_keep, backend, main_file)

    def initialize(self, contents, metainfo_to_keep, backend, main_file):
        """Initialize the parser with the given environment.
        """
        self.parser_context = ParserContext()
        self.parser_context.backend = backend
        self.parser_context.metainfo_to_keep = metainfo_to_keep
        self.parser_context.main_file = main_file
        self.implementation = None

        # If single path provided, make it into a list
        if isinstance(contents, basestring):
            contents = [contents]

        if contents:
            # Use a set as it will automatically ignore duplicates (nested
            # folders may have been included)
            files = set()

            for content in contents:
                # Add all files recursively from a directory
                found_files = []
                if os.path.isdir(content):
                    for root, dirnames, filenames in os.walk(content):
                        for filename in filenames:
                            filename = os.path.join(root, filename)
                            found_files.append(filename)
                    files |= set(found_files)
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
        to the parser implementation. By default does not do any filtering.
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

        self.implementation.parse()


#===============================================================================
class ParserImplementation(object):
    """The base class for a version specific parser implementation in. Provides
    some useful tools for setting up file access.

    Attributes:
        See the ParserContext class for more details about the attributes.
        _file_handles: A "private" dictionary containing the cached file handles
        _file_contents: A "private" dictionary containing the cached file contents
        _file_sizes: A "private" dictionary containing the cached file sizes
        file_ids: A dictionary containing the mapping between file ids and filepaths
    """
    def __init__(self, parser_context):

        self.parser_context = parser_context

        # Copy all the attributes from the ParserContext object for quick access
        attributes = dir(parser_context)
        for attribute in attributes:
            if not attribute.startswith("__"):
                setattr(self, attribute, getattr(parser_context, attribute))

        self._file_handles = {}
        self._file_contents = {}
        self._file_sizes = {}
        self.file_ids = {}
        self.file_parsers = []

    def setup_given_file_ids(self):
        """Saves the file id's that were given in the JSON input.
        """
        for path, file_id in self.files.iteritems():
            if file_id:
                self.setup_file_id(path, file_id)

    def parse(self):
        """Start the parsing. Will try to parse everything unless given special
        rules (metaInfoToKeep)."""
        for file_parser in self.file_parsers:
            file_parser.parse()

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
class FileParser(object):
    """Base class for objects that parse certain type of files.  Typically a
    subclass of ParserImplementation will initialize one FileParser per parsed
    file. You can also assign a list of files to a FileParser if they are of
    similar type or are otherwise connected to each other.
    """
    __metaclass__ = ABCMeta

    def __init__(self, files, parser_context):
        """
        Args:
            files: A list of filenames that are parsed and analyzed by this
                object.
            parser_context: The parsing context that contains e.g. the backend.
        """
        if not isinstance(files, list):
            files = [files]
        self.files = files
        if parser_context:
            self.parser_context = parser_context
            self.backend = parser_context.backend
            self.metainfo_to_keep = parser_context.metainfo_to_keep
            self.version_id = parser_context.version_id
        self.root_matcher = None
        self.caching_level_for_metaName = {}
        self.default_data_caching_level = CachingLevel.ForwardAndCache
        self.default_section_caching_level = CachingLevel.Forward
        self.onClose = {}

    def parse(self):
        """Parser the information from the given file(s). By default uses the
        SimpleParser scheme, if you want to use something else or customize the
        process just override this method.
        """
        # If there is only one file assigned to this FileParser, and a
        # root_matcher has been assigned, parse with the SimpleParser. Otherwise
        # halt.
        if len(self.files) != 1 or self.root_matcher is None:
            logger.error("Could not use the default parsing implementation. If you want to use it wou must specify a root_matcher and only assign one file to the FileParser. If you need custom parsing you should override the parse() method.")
            return

        # Initialize the parser builder
        parserBuilder = SimpleParserBuilder(self.root_matcher, self.backend.metaInfoEnv(), self.metainfo_to_keep)

        # Verify the metainfo
        if not parserBuilder.verifyMetaInfo(sys.stderr):
            sys.exit(1)

        # Gather onClose functions from supercontext
        onClose = dict(self.onClose)
        for attr, callback in extractOnCloseTriggers(self).items():
            oldCallbacks = onClose.get(attr, None)
            if oldCallbacks:
                oldCallbacks.append(callback)
            else:
                onClose[attr] = [callback]

        # Setup the backend that caches ond handles triggers
        active_backend = ActiveBackend.activeBackend(
            metaInfoEnv=self.backend.metaInfoEnv(),
            cachingLevelForMetaName=self.caching_level_for_metaname,
            defaultDataCachingLevel=self.default_data_caching_level,
            defaultSectionCachingLevel=self.default_section_caching_level,
            onClose=onClose,
            superBackend=self.backend)

        # Compile the SimpleMatcher tree
        parserBuilder.compile()

        fileToParse = self.files[0]
        self.backend.fileOut.write("[")
        uri = "file://" + fileToParse
        parserInfo = {'name': 'cp2k-parser', 'version': '1.0'}
        active_backend.startedParsingSession(uri, parserInfo)
        with open(fileToParse, "r") as fIn:
            parser = parserBuilder.buildParser(PushbackLineFile(fIn), active_backend, superContext=self)
            parser.parse()
        active_backend.finishedParsingSession("ParseSuccess", None)
        self.backend.fileOut.write("]\n")

    def get_metainfos(self):
        """Get a list of all the metainfo names that are parsed by this
        FileParser. This information is used by the ParserImplementation to
        optimize the parsing process according to the given 'metainfo_to_keep'
        list.
        """
        return self.root_matcher.allMetaNames()

    def startedParsing(self, fInName, parser):
        """Function is called when the parsing starts.

        Get compiled parser.
        Later one can compile a parser for parsing an external file.
        """
        self.parser = parser


#===============================================================================
class ParserContext(object):
    """Contains everything needed to instantiate a parser implementation.
    """
    def __init__(self, files=None, metainfo_to_keep=None, backend=None, version_id=None, main_file=None):
        self.files = files
        self.version_id = version_id
        self.metainfo_to_keep = metainfo_to_keep
        self.backend = backend
        self.main_file = main_file
