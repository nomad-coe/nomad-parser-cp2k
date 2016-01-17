import os
import logging
from abc import ABCMeta, abstractmethod
from nomadcore.local_meta_info import loadJsonFile
logger = logging.getLogger(__name__)


#===============================================================================
class Parser(object):
    """
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
        self.parser_context = ParserContext()
        self.parser_context.backend = backend
        self.parser_context.metainfo_to_keep = metainfo_to_keep
        self.implementation = None

        # If single path provided, make it into a list
        if isinstance(contents, basestring):
            contents = [contents]

        # Figure out all the files from the contents
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

    @abstractmethod
    def parse(self):
        """Starts the actual parsing process outputting the results to the
        backend.
        """
        self.setup()
        if not self.implementation:
            logger.error("No parser implementation has been setup.")


#===============================================================================
class ParserContext(object):
    """Contains everything needed to instantiate a parser implementation.
    """
    def __init__(self, files=None, metainfo_to_keep=None, backend=None, version_id=None):
        self.files = files
        self.version_id = version_id
        self.metainfo_to_keep = metainfo_to_keep
        self.backend = backend
