import re
from cp2kparser.generics.parserversioner import ParserVersioner
from cp2kparser.implementation.implementations import *
import logging
logger = logging.getLogger(__name__)


#===============================================================================
class CP2KParserVersioner(ParserVersioner):
    """Builds the correct parser by looking at the given files and the given
    input.

    This class handles the initial setup before any parsing can happen. It
    determines which version of CP2K was used to generate the output and then
    sets up a correct implementation.
    """
    def __init__(self, input_json_string, stream):
        ParserVersioner.__init__(self, input_json_string, stream)

    def build_parser(self):
        """Setups the version by looking at the output file and the version
        specified in it.
        """
        # Search for the output file
        count = 0
        for filepath in self.parser_context.files.iterkeys():
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

        # Search for a version specific implementation
        class_name = "CP2KImplementation{}".format(self.parser_context.version_id)
        class_object = globals().get(class_name)
        if class_object:
            logger.debug("Using version specific implementation '{}'.".format(class_name))
            self.implementation = class_object(self.parser_context)
        else:
            logger.debug("No version specific implementation found. Using the default implementation: {}".format(class_name))
            self.parser_context.version_id = "262"
            self.implementation = globals()["CP2KImplementation262"](self.parser_context)

        return self.implementation
