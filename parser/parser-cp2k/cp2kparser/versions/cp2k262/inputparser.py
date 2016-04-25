import os
import logging
import cPickle as pickle
from cp2kparser.generic.baseclasses import BasicParser
from cp2kparser.generic.inputparsing import *
logger = logging.getLogger("nomad")


#===============================================================================
class CP2KInputParser(BasicParser):
    """Used to parse out a CP2K input file.

    When given a filepath to a CP2K input file, this class attemts to parse
    it's contents.
    """
    def __init__(self, file_path, parser_context):
        super(CP2KInputParser, self).__init__(file_path, parser_context)
        self.root_section = None
        self.input_tree = None

    def parse(self):

        # Gather the information from the input file
        self.fill_input_tree(self.file_path)

        #=======================================================================
        # Parse the used XC_functionals and their parameters
        xc = self.input_tree.get_section("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL")
        if xc is not None:
            xc_list = []

            class XCFunctional(object):
                def __init__(self, name, weight=1, parameters=None):
                    self.name = name
                    self.weight = weight
                    self.parameters = parameters

            # First see if a functional has been specified in the section parameter
            section_parameter = xc.section_parameter.value
            if section_parameter is not None:

                if section_parameter == "BLYP":
                    xc_list.append(XCFunctional("GGA_X_B88"))
                    xc_list.append(XCFunctional("GGA_C_LYP"))

                elif section_parameter == "LDA" or section_parameter == "PADE":
                    xc_list.append(XCFunctional("LDA_XC_TETER93"))

                elif section_parameter == "PBE":
                    xc_list.append(XCFunctional("GGA_X_PBE"))
                    xc_list.append(XCFunctional("GGA_C_PBE"))

                elif section_parameter == "OLYP":
                    xc_list.append(XCFunctional("GGA_X_OPTX"))
                    xc_list.append(XCFunctional("GGA_C_LYP"))

                elif section_parameter == "HCTH120":
                    xc_list.append(XCFunctional("GGA_XC_HCTH_120"))

                elif section_parameter == "PBE0":
                    xc_list.append(XCFunctional("HYB_GGA_XC_PBEH"))

                elif section_parameter == "B3LYP":
                    xc_list.append(XCFunctional("HYB_GGA_XC_B3LYP"))

                else:
                    logger.warning("Unknown XC functional given in XC_FUNCTIONAL section parameter.")

            # Otherwise one has to look at the individual functional settings
            else:
                pass

            # Sort the functionals alphabetically by name
            xc_list.sort(key=lambda x: x.name)
            xc_summary = ""

            # For every defined functional, stream the information to the
            # backend and construct the summary string
            for i, functional in enumerate(xc_list):

                gId = self.backend.openSection("section_XC_functionals")
                self.backend.addValue("XC_functional_name", functional.name)
                self.backend.addValue("XC_functional_weight", functional.weight)
                if functional.parameters is not None:
                    pass
                self.backend.closeSection("section_XC_functionals", gId)

                if i != 0:
                    xc_summary += "+"
                xc_summary += "{}*{}".format(functional.weight, functional.name)
                if functional.parameters is not None:
                    xc_summary += ":{}".format()

            # Stream summary
            if xc_summary is not "":
                self.backend.addValue("XC_functional", xc_summary)

        #=======================================================================
        # Cell periodicity
        periodicity = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/PERIODIC").upper()
        periodicity_list = None
        if periodicity == "NONE":
            periodicity_list = (False, False, False)
        elif periodicity == "X":
            periodicity_list = (True, False, False)
        elif periodicity == "XY":
            periodicity_list = (True, True, False)
        elif periodicity == "XYZ":
            periodicity_list = (True, True, True)
        elif periodicity == "XZ":
            periodicity_list = (True, False, True)
        elif periodicity == "Y":
            periodicity_list = (False, True, False)
        elif periodicity == "YZ":
            periodicity_list = (False, True, True)
        elif periodicity == "Z":
            periodicity_list = (False, False, True)
        if periodicity_list is not None:
            self.backend.addValue("configuration_periodic_dimensions", periodicity_list)
        else:
            logger.warning("Could not determine cell periodicity from FORCE_EVAL/SUBSYS/CELL/PERIODIC")

    def fill_input_tree(self, file_path):
        """Parses a CP2K input file into an object tree.

        Return an object tree represenation of the input augmented with the
        default values and lone keyword values from the cp2k_input.xml file
        which is version specific. Keyword aliases are also mapped to the same
        data.

        The cp2k input is largely case-insensitive. In the input tree, we wan't
        only one standard way to name things, so all section names and section
        parameters will be transformed into upper case.

        To query the returned tree use the following functions:
            get_keyword("GLOBAL/PROJECT_NAME")
            get_parameter("GLOBAL/PRINT")
            get_default_keyword("FORCE_EVAL/SUBSYS/COORD")

        Args:
            : A string containing the contents of a CP2K input file. The
            input file can be stored as string as it isn't that big.

        Returns:
            The input as an object tree.
        """

        self.setup_version(self.parser_context.version_id)
        section_stack = []

        with open(file_path) as inp:
            for line in inp:
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
                    name = parts[0][1:].upper()
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
                        self.input_tree.set_parameter(path, parts[1].strip().upper())

                # Contents (keywords, default keywords)
                else:
                    split = line.split(' ', 1)
                    keyword_name = split[0].upper()
                    keyword_value = split[1]
                    self.input_tree.set_keyword(path + "/" + keyword_name, keyword_value)

    def setup_version(self, version_number):
        """ The pickle file which contains preparsed data from the
        cp2k_input.xml is version specific. By calling this function before
        parsing the correct file can be found.
        """
        pickle_path = os.path.dirname(__file__) + "/input_data/cp2k_input_tree.pickle".format(version_number)
        input_tree_pickle_file = open(pickle_path, 'rb')
        self.input_tree = pickle.load(input_tree_pickle_file)
