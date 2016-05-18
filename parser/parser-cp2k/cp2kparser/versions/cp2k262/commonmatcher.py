import re
import numpy as np
import logging
from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.simple_parser import extractOnCloseTriggers
from nomadcore.caching_backend import CachingLevel
from inputparser import CP2KInputParser
logger = logging.getLogger("nomad")


#===============================================================================
class CommonMatcher(object):
    """
    This class is used to store and instantiate common parts of the
    hierarchical SimpleMatcher structure used in the parsing of a CP2K
    output file.
    """
    def __init__(self, parser_context):

        # Repeating regex definitions
        self.parser_context = parser_context
        self.file_service = parser_context.file_service
        self.regex_f = "-?\d+\.\d+(?:E(?:\+|-)\d+)?"  # Regex for a floating point value
        self.regex_i = "-?\d+"  # Regex for an integer

        self.caching_levels = {
            'section_XC_functionals': CachingLevel.ForwardAndCache,
            'self_interaction_correction_method': CachingLevel.Cache,
            'x_cp2k_section_md_coordinates': CachingLevel.Cache,
            'x_cp2k_section_md_coordinate_atom': CachingLevel.Cache,
            'x_cp2k_md_coordinate_atom_string': CachingLevel.Cache,
            'x_cp2k_md_coordinate_atom_float': CachingLevel.Cache,

            'x_cp2k_section_md_forces': CachingLevel.Cache,
            'x_cp2k_section_md_force_atom': CachingLevel.Cache,
            'x_cp2k_md_force_atom_string': CachingLevel.Cache,
            'x_cp2k_md_force_atom_float': CachingLevel.Cache,
        }

    #===========================================================================
    # SimpleMatcher trees

    # SimpleMatcher for the header that is common to all run types
    def header(self):
        return SM(r" DBCSR\| Multiplication driver",
            forwardMatch=True,
            subMatchers=[
                SM( r" DBCSR\| Multiplication driver",
                    sections=['x_cp2k_section_dbcsr'],
                ),
                SM( r" \*\*\*\* \*\*\*\* \*\*\*\*\*\*  \*\*  PROGRAM STARTED AT\s+(?P<x_cp2k_run_start_date>\d{4}-\d{2}-\d{2}) (?P<x_cp2k_run_start_time>\d{2}:\d{2}:\d{2}.\d{3})",
                    sections=['x_cp2k_section_startinformation'],
                ),
                SM( r" CP2K\|",
                    sections=['x_cp2k_section_programinformation'],
                    forwardMatch=True,
                    subMatchers=[
                        SM( r" CP2K\| version string:\s+(?P<program_version>[\w\d\W\s]+)"),
                        SM( r" CP2K\| source code revision number:\s+svn:(?P<x_cp2k_svn_revision>\d+)"),
                    ]
                ),
                SM( r" CP2K\| Input file name\s+(?P<x_cp2k_input_filename>.+$)",
                    sections=['x_cp2k_section_filenames'],
                    otherMetaInfo=['section_XC_functionals', 'XC_functional_name', 'XC_functional_weight', 'XC_functional', 'configuration_periodic_dimensions', "stress_tensor_method"],
                    subMatchers=[
                        SM( r" GLOBAL\| Basis set file name\s+(?P<x_cp2k_basis_set_filename>.+$)"),
                        SM( r" GLOBAL\| Geminal file name\s+(?P<x_cp2k_geminal_filename>.+$)"),
                        SM( r" GLOBAL\| Potential file name\s+(?P<x_cp2k_potential_filename>.+$)"),
                        SM( r" GLOBAL\| MM Potential file name\s+(?P<x_cp2k_mm_potential_filename>.+$)"),
                        SM( r" GLOBAL\| Coordinate file name\s+(?P<x_cp2k_coordinate_filename>.+$)"),
                    ]
                ),
                SM( " CELL\|",
                    adHoc=self.adHoc_cp2k_section_cell(),
                    otherMetaInfo=["simulation_cell"]
                ),
                SM( " DFT\|",
                    otherMetaInfo=["XC_functional", "self_interaction_correction_method"],
                    forwardMatch=True,
                    subMatchers=[
                        SM( " DFT\| Multiplicity\s+(?P<target_multiplicity>{})".format(self.regex_i)),
                        SM( " DFT\| Charge\s+(?P<total_charge>{})".format(self.regex_i)),
                        SM( " DFT\| Self-interaction correction \(SIC\)\s+(?P<self_interaction_correction_method>[^\n]+)"),
                    ]
                ),
                SM( " TOTAL NUMBERS AND MAXIMUM NUMBERS",
                    sections=["x_cp2k_section_total_numbers"],
                    subMatchers=[
                        SM( "\s+- Atoms:\s+(?P<number_of_atoms>\d+)"),
                        SM( "\s+- Shell sets:\s+(?P<x_cp2k_shell_sets>\d+)")
                    ]
                )
            ]
        )

    #===========================================================================
    # Section close triggers
    def onClose_section_method(self, backend, gIndex, section):
        """When all the functional definitions have been gathered, matches them
        with the nomad correspondents and combines into one single string which
        is put into the backend.
        """
        # Transform the CP2K self-interaction correction string to the NOMAD
        # correspondent, and push directly to the superBackend to avoid caching
        try:
            sic_cp2k = section["self_interaction_correction_method"][0]
            sic_map = {
                "NO": "",
                "AD SIC": "SIC_AD",
                "Explicit Orbital SIC": "SIC_EXPLICIT_ORBITALS",
                "SPZ/MAURI SIC": "SIC_MAURI_SPZ",
                "US/MAURI SIC": "SIC_MAURI_US",
            }
            sic_nomad = sic_map.get(sic_cp2k)
            if sic_nomad is not None:
                backend.superBackend.addValue('self_interaction_correction_method', sic_nomad)
            else:
                logger.warning("Unknown self-interaction correction method used.")
        except:
            pass

    def onClose_x_cp2k_section_filenames(self, backend, gIndex, section):
        """
        """
        # If the input file is available, parse it
        input_file = section["x_cp2k_input_filename"][0]
        filepath = self.file_service.get_absolute_path_to_file(input_file)
        if filepath is not None:
            input_parser = CP2KInputParser(filepath, self.parser_context)
            input_parser.parse()
        else:
            logger.warning("The input file of the calculation could not be found.")

    #===========================================================================
    # Ad hoc parsing
    def adHoc_cp2k_section_cell(self):
        """Used to extract the cell information.
        """
        def wrapper(parser):
            # Read the lines containing the cell vectors
            a_line = parser.fIn.readline()
            b_line = parser.fIn.readline()
            c_line = parser.fIn.readline()

            # Define the regex that extracts the components and apply it to the lines
            regex_string = r" CELL\| Vector \w \[angstrom\]:\s+({0})\s+({0})\s+({0})".format(self.regex_f)
            regex_compiled = re.compile(regex_string)
            a_result = regex_compiled.match(a_line)
            b_result = regex_compiled.match(b_line)
            c_result = regex_compiled.match(c_line)

            # Convert the string results into a 3x3 numpy array
            cell = np.zeros((3, 3))
            cell[0, :] = [float(x) for x in a_result.groups()]
            cell[1, :] = [float(x) for x in b_result.groups()]
            cell[2, :] = [float(x) for x in c_result.groups()]

            # Push the results to the correct section
            parser.backend.addArrayValues("simulation_cell", cell, unit="angstrom")
        return wrapper

    def getOnCloseTriggers(self):
        """
        Returns:
            A dictionary containing a section name as a key, and a list of
            trigger functions associated with closing that section.
        """
        onClose = {}
        for attr, callback in extractOnCloseTriggers(self).items():
            onClose[attr] = [callback]
        return onClose
