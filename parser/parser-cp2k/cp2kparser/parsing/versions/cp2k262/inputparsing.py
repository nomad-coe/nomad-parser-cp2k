import os
import logging
import cPickle as pickle
logger = logging.getLogger(__name__)


#===============================================================================
class CP2KInputParser(object):
    """Used to parse out a CP2K input file.

    When given a file handle to a CP2K input file, this class attemts to parse
    out it's structure into an accessible object tree.
    """
    def __init__(self):
        self.root_section = None
        self.input_tree = None

    def parse(self, inp):
        """Parses a CP2K input file into an object tree.

        Return an object tree represenation of the input augmented with the
        default values and lone keyword values from the cp2k_input.xml file
        which is version specific. Keyword aliases are also mapped to the same data.

        To query the returned tree use the following functions:
            get_keyword("GLOBAL/PROJECT_NAME")
            get_parameter("GLOBAL/PRINT")
            get_default_keyword("FORCE_EVAL/SUBSYS/COORD")

        Args:
            inp: A string containing the contents of a CP2K input file. The
            input file can be stored as string as it isn't that big.

        Returns:
            The input as an object tree.
        """
        # See if version is setup
        if self.input_tree is None:
            logger.error("Please setup the CP2K version before parsing")
            return

        section_stack = []

        for line in inp.split('\n'):
            line = line.split('!', 1)[0].strip()

            # Skip empty lines
            if len(line) == 0:
                continue

            # Section ends
            if line.upper().startswith('&END'):
                section_stack.pop()
            # Section starts
            elif line[0] == '&':
                parts = line.split(' ', 1)
                name = parts[0][1:]
                section_stack.append(name)

                # Form the path
                path = ""
                for index, item in enumerate(section_stack):
                    if index != 0:
                        path += '/'
                    path += item

                # Mark the section as accessed.
                self.input_tree.set_section_accessed(path)

                # Save the section parameters
                if len(parts) > 1:
                    self.input_tree.set_parameter(path, parts[1].strip())
            # Contents (keywords, default keywords)
            else:
                split = line.split(' ', 1)
                keyword_name = split[0]
                keyword_value = split[1]
                self.input_tree.set_keyword(path + "/" + keyword_name, keyword_value)

        return self.input_tree

    def setup_version(self, version_number):
        """ The pickle file which contains preparsed data from the
        cp2k_input.xml is version specific. By calling this function before
        parsing the correct file can be found.
        """
        pickle_path = os.path.dirname(__file__) + "/input_xml/cp2k_input_tree.pickle".format(version_number)
        input_tree_pickle_file = open(pickle_path, 'rb')
        self.input_tree = pickle.load(input_tree_pickle_file)
