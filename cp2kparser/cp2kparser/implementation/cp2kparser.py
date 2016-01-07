import re
import logging
from ..generics.parser import Parser
from ..implementation.cp2kimplementations import *
logger = logging.getLogger(__name__)


#===============================================================================
class CP2KParser(Parser):
    """Builds the correct parser by looking at the given files and the given
    input.

    This class handles the initial setup before any parsing can happen. It
    determines which version of CP2K was used to generate the output and then
    sets up a correct implementation.

    After the implementation has been setup, you can parse the files with
    parse().
    """
    def __init__(self, dirpath=None, files=None, metainfo_path=None, backend=None):
        Parser.__init__(self, dirpath, files, metainfo_path, backend)

    def setup(self):
        """Setups the version by looking at the output file and the version
        specified in it.
        """
        # Search for the output file
        count = 0
        for filepath in self.parser_context.files:
            if filepath.endswith(".out"):
                count += 1
                outputpath = filepath
        if count > 1:
            logger("Could not determine the correct outputfile because multiple files with extension '.out' were found.")
            return
        elif count == 0:
            logger.error("No output file could be found. The outputfile should have a '.out' extension.")
            return

        # Search for the version specification
        outputfile = open(outputpath, 'r')
        regex = re.compile(r" CP2K\| version string:\s+CP2K version ([\d\.]+)")
        for line in outputfile:
            result = regex.match(line)
            if result:
                self.parser_context.version_id = result.group(1).replace('.', '')
                break

        # Search and initialize a version specific implementation
        class_name = "CP2KImplementation{}".format(self.parser_context.version_id)
        class_object = globals().get(class_name)
        if class_object:
            logger.debug("Using version specific implementation '{}'.".format(class_name))
            self.implementation = class_object(self.parser_context)
        else:
            logger.debug("No version specific implementation found. Using the default implementation: {}".format(class_name))
            self.parser_context.version_id = "262"
            self.implementation = globals()["CP2KImplementation262"](self.parser_context)

    def parse(self):
        self.setup()
        self.implementation.parse()
