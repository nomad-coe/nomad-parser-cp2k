import os
import re
import logging
from cp2kparser.generic.baseclasses import ParserInterface
from cp2kparser.versions.versionsetup import get_main_parser
logger = logging.getLogger(__name__)


#===============================================================================
class CP2KParser(ParserInterface):
    """This class handles the initial setup before any parsing can happen. It
    determines which version of CP2K was used to generate the output and then
    sets up a correct implementation.

    After the implementation has been setup, you can parse the files with
    parse().
    """
    def __init__(self, main_file, metainfo_to_keep=None, backend=None, default_units=None, metainfo_units=None):
        super(CP2KParser, self).__init__(main_file, metainfo_to_keep, backend, default_units, metainfo_units)

    def setup_version(self):
        """Setups the version by looking at the output file and the version
        specified in it.
        """
        # Search for the version specification and initialize a correct
        # main parser for this version.
        regex = re.compile(r" CP2K\| version string:\s+CP2K version ([\d\.]+)")
        n_lines = 30
        with open(self.parser_context.main_file, 'r') as outputfile:
            for i_line in xrange(n_lines):
                line = next(outputfile)
                result = regex.match(line)
                if result:
                    version_id = result.group(1).replace('.', '')
                    break
        if not result:
            logger.error("Could not find a version specification from the given main file.")

        # Setup the root folder to the fileservice that is used to access files
        dirpath, filename = os.path.split(self.parser_context.main_file)
        self.parser_context.file_service.setup_root_folder(dirpath)
        self.parser_context.file_service.set_file_id(filename, "output")

        # Setup the correct main parser based on the version id. If no match
        # for the version is found, use the main parser for CP2K 2.6.2
        self.main_parser = get_main_parser(version_id)(self.parser_context.main_file, self.parser_context)

    def get_metainfo_filename(self):
        return "cp2k.nomadmetainfo.json"

    def get_parser_info(self):
        return {'name': 'cp2k-parser', 'version': '1.0'}
