import os
import logging
from abc import ABCMeta, abstractmethod
from nomadanalysis.local_backend import LocalBackend
logger = logging.getLogger(__name__)


#===============================================================================
class Parser(object):
    """
    """
    __metaclass__ = ABCMeta

    def __init__(self, dirpath=None, files=None, metainfo_to_keep=None, backend=None):
        """
        """
        self.parser_context = ParserContext()
        self.parser_context.backend = backend
        self.parser_context.files = files
        self.parser_context.backend = backend
        self.parser_context.metainfo_to_keep = metainfo_to_keep
        self.implementation = None

        # If directory provided, the interesting files are first identified
        if dirpath:
            files = self.search_path(dirpath)
            self.parser_context.files = files

        # If no backend provided, create one with default metainfos
        if not backend:
            metainfo_path = "/home/lauri/Dropbox/nomad-dev/nomad-meta-info/meta_info/nomad_meta_info/cp2k.nomadmetainfo.json"
            metainfoenv, warnings = loadJsonFile(metainfo_path)
            backend = LocalBackend(metainfoenv)
            self.parser_context.backend = LocalBackend()

    @abstractmethod
    def setup(self):
        """Deduce the version of the software that was used and setup a correct
        implementation. The implementations should subclass NomadParser.

        Returns:
            A NomadParser object that is ready to do the parsing.
        """
        pass

    def search_path(self, dirpath):
        """Searches the given path for files that are of interest to this
        parser. Returns them as a list of path strings.
        """
        files = []
        for filename in os.listdir(dirpath):
            files.append(os.path.join(dirpath, filename))
        return files


#===============================================================================
class ParserContext(object):
    """Contains everything needed to instantiate a parser implementation.
    """
    def __init__(self, files=None, metainfo_to_keep=None, backend=None, version_id=None):
        self.files = files
        self.version_id = version_id
        self.metainfo_to_keep = metainfo_to_keep
        self.backend = backend
