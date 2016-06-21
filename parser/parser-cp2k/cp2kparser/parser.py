from builtins import next
from builtins import range
import os
import re
import logging
from nomadcore.baseclasses import ParserInterface
from cp2kparser.versions.versionsetup import get_main_parser
logger = logging.getLogger("nomad")


#===============================================================================
class CP2KParser(ParserInterface):
    """This class handles the initial setup before any parsing can happen. It
    determines which version of CP2K was used to generate the output and then
    sets up a correct main parser.

    After the implementation has been setup, you can parse the files with
    parse().
    """
    def __init__(self, main_file, metainfo_to_keep=None, backend=None, default_units=None, metainfo_units=None, debug=True, store=True):
        super(CP2KParser, self).__init__(main_file, metainfo_to_keep, backend, default_units, metainfo_units, debug, store)

    def setup_version(self):
        """Setups the version by looking at the output file and the version
        specified in it.
        """
        # Search for the CP2K version specification and the RUN_TYPE for the
        # calculation. The correct and optimized parser is initialized based on
        # this information.
        regex_version = re.compile(r" CP2K\| version string:\s+CP2K version ([\d\.]+)")
        regex_run_type = re.compile(r"\s+GLOBAL\| Run type\s+(.+)")
        n_lines = 50
        version_id = None
        run_type = None
        with open(self.parser_context.main_file, 'r') as outputfile:
            for i_line in range(n_lines):
                line = next(outputfile)
                result_version = regex_version.match(line)
                result_run_type = regex_run_type.match(line)
                if result_version:
                    version_id = result_version.group(1).replace('.', '')
                if result_run_type:
                    run_type = result_run_type.group(1)
        if version_id is None:
            msg = "Could not find a version specification from the given main file."
            logger.exception(msg)
            raise RuntimeError(msg)
        if run_type is None:
            msg = "Could not find a version specification from the given main file."
            logger.exception(msg)
            raise RuntimeError(msg)

        # Setup the root folder to the fileservice that is used to access files
        dirpath, filename = os.path.split(self.parser_context.main_file)
        dirpath = os.path.abspath(dirpath)
        self.parser_context.file_service.setup_root_folder(dirpath)
        self.parser_context.file_service.set_file_id(filename, "output")

        # Setup the correct main parser based on the version id. If no match
        # for the version is found, use the main parser for CP2K 2.6.2
        self.main_parser = get_main_parser(version_id, run_type)(self.parser_context.main_file, self.parser_context)

    def get_metainfo_filename(self):
        return "cp2k.nomadmetainfo.json"

    def get_parser_info(self):
        return {'name': 'cp2k-parser', 'version': '1.0'}
