import re
from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.caching_backend import CachingLevel
from nomadcore.baseclasses import MainHierarchicalParser
from singlepointforceparser import CP2KSinglePointForceParser
from commonmatcher import CommonMatcher
import numpy as np
import logging
logger = logging.getLogger("nomad")


#===============================================================================
class CP2KSinglePointParser(MainHierarchicalParser):
    """The main parser class. Used to parse the CP2K calculation with run types:
        -ENERGY
        -ENERGY_FORCE
    """
    def __init__(self, file_path, parser_context):
        """
        """
        super(CP2KSinglePointParser, self).__init__(file_path, parser_context)
        self.scf_iterations = 0
        self.cm = CommonMatcher(parser_context)
        self.section_method_index = None
        self.section_system_description_index = None

        # Simple matcher for run type ENERGY_FORCE, ENERGY with QUICKSTEP
        self.energy_force = SM(
            " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
            forwardMatch=True,
            subMatchers=[
                SM( " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
                    adHoc=self.adHoc_cp2k_section_quickstep_atom_information(),
                    otherMetaInfo=["atom_label", "atom_position"]
                ),
                SM( " SCF WAVEFUNCTION OPTIMIZATION",
                    subMatchers=[
                        SM( r"  Trace\(PS\):",
                            sections=["section_scf_iteration"],
                            repeats=True,
                            subMatchers=[
                                SM( r"  Exchange-correlation energy:\s+(?P<energy_XC_scf_iteration__hartree>{})".format(self.cm.regex_f)),
                                SM( r"\s+\d+\s+\S+\s+{0}\s+{0}\s+{0}\s+(?P<energy_total_scf_iteration__hartree>{0})\s+(?P<energy_change_scf_iteration__hartree>{0})".format(self.cm.regex_f)),
                            ]
                        ),
                        SM( r"  \*\*\* SCF run converged in\s+(\d+) steps \*\*\*",
                            adHoc=self.adHoc_single_point_converged()
                        ),
                        SM( r"  \*\*\* SCF run NOT converged \*\*\*",
                            adHoc=self.adHoc_single_point_not_converged()
                        ),
                        SM( r"  Electronic kinetic energy:\s+(?P<electronic_kinetic_energy__hartree>{})".format(self.cm.regex_f)),
                        SM( r" ENERGY\| Total FORCE_EVAL \( \w+ \) energy \(a\.u\.\):\s+(?P<energy_total__hartree>{0})".format(self.cm.regex_f)),
                        SM( r" ATOMIC FORCES in \[a\.u\.\]"),
                        SM( r" # Atom   Kind   Element          X              Y              Z",
                            adHoc=self.adHoc_atom_forces()
                        ),
                    ]
                )
            ]
        )

        # Compose root matcher according to the run type. This way the
        # unnecessary regex parsers will not be compiled and searched. Saves
        # computational time.
        self.root_matcher = SM("",
            forwardMatch=True,
            sections=['section_run', "section_single_configuration_calculation", "section_system_description", "section_method"],
            subMatchers=[
                self.cm.header(),
                self.energy_force
            ]
        )
        #=======================================================================
        # The cache settings
        self.caching_level_for_metaname = {
            'section_XC_functionals': CachingLevel.ForwardAndCache,
            'self_interaction_correction_method': CachingLevel.Cache,
            'cp2k_section_md_coordinates': CachingLevel.Cache,
            'cp2k_section_md_coordinate_atom': CachingLevel.Cache,
            'cp2k_md_coordinate_atom_string': CachingLevel.Cache,
            'cp2k_md_coordinate_atom_float': CachingLevel.Cache,

            'cp2k_section_md_forces': CachingLevel.Cache,
            'cp2k_section_md_force_atom': CachingLevel.Cache,
            'cp2k_md_force_atom_string': CachingLevel.Cache,
            'cp2k_md_force_atom_float': CachingLevel.Cache,
        }

        #=======================================================================
        # The additional onClose trigger functions
        self.onClose = self.cm.getOnCloseTriggers()

    #===========================================================================
    # onClose triggers. These are specific to this main parser, common
    # triggers are imprted from commonmatchers module.
    def onClose_section_scf_iteration(self, backend, gIndex, section):
        """Keep track of how many SCF iteration are made."""
        self.scf_iterations += 1

    def onClose_section_system_description(self, backend, gIndex, section):
        """Stores the index of the section method. Should always be 0, but
        let's get it dynamically just in case there's something wrong.
        """
        self.section_system_description_index = gIndex

    def onClose_section_method(self, backend, gIndex, section):
        """Stores the index of the section method. Should always be 0, but
        let's get it dynamically just in case there's something wrong.
        """
        self.section_method_index = gIndex

    def onClose_section_single_configuration_calculation(self, backend, gIndex, section):
        """
        """
        # If the force file for a single point calculation is available, and
        # the forces were not parsed fro the output file, parse the separate
        # file
        if section["atom_forces"] is None:
            force_file = self.file_service.get_file_by_id("force_file_single_point")
            if force_file is not None:
                force_parser = CP2KSinglePointForceParser(force_file, self.parser_context)
                force_parser.parse()
            else:
                logger.warning("The file containing the forces printed by ENERGY_FORCE calculation could not be found.")

        # Output the number of SCF iterations made
        backend.addValue("scf_dft_number_of_iterations", self.scf_iterations)

        # Write the references to section_method and section_system_description
        backend.addValue('single_configuration_to_calculation_method_ref', self.section_method_index)
        backend.addValue('single_configuration_calculation_to_system_description_ref', self.section_system_description_index)

    #===========================================================================
    # adHoc functions. Primarily these
    # functions are used for data that is formatted as a table or a list.
    def adHoc_section_XC_functionals(self):
        """Used to extract the functional information.
        """
        def wrapper(parser):

            # Define the regex that extracts the information
            regex_string = " FUNCTIONAL\| ([\w\d\W\s]+):"
            regex_compiled = re.compile(regex_string)

            # Parse out the functional name
            functional_name = None
            line = parser.fIn.readline()
            result = regex_compiled.match(line)

            if result:
                functional_name = result.groups()[0]

            # Define a mapping for the functionals
            functional_map = {
                "LYP": "GGA_C_LYP",
                "BECKE88": "GGA_X_B88",
                "PADE": "LDA_XC_TETER93",
                "LDA": "LDA_XC_TETER93",
                "BLYP": "HYB_GGA_XC_B3LYP",
            }

            # If match found, add the functional definition to the backend
            nomad_name = functional_map.get(functional_name)
            if nomad_name is not None:
                parser.backend.addValue('XC_functional_name', nomad_name)

        return wrapper

    def adHoc_cp2k_section_quickstep_atom_information(self):
        """Used to extract the initial atomic coordinates and names in the
        Quickstep module.
        """
        def wrapper(parser):

            # Define the regex that extracts the information
            regex_string = r"\s+\d+\s+\d+\s+(\w+)\s+\d+\s+({0})\s+({0})\s+({0})".format(self.cm.regex_f)
            regex_compiled = re.compile(regex_string)

            match = True
            coordinates = []
            labels = []

            # Currently these three lines are not processed
            parser.fIn.readline()
            parser.fIn.readline()
            parser.fIn.readline()

            while match:
                line = parser.fIn.readline()
                result = regex_compiled.match(line)

                if result:
                    match = True
                    label = result.groups()[0]
                    labels.append(label)
                    coordinate = [float(x) for x in result.groups()[1:]]
                    coordinates.append(coordinate)
                else:
                    match = False
            coordinates = np.array(coordinates)
            labels = np.array(labels)

            # If anything found, push the results to the correct section
            if len(coordinates) != 0:
                parser.backend.addArrayValues("atom_position", coordinates, unit="angstrom")
                parser.backend.addArrayValues("atom_label", labels)

        return wrapper

    def adHoc_atom_forces(self):
        """Used to extract the final atomic forces printed at the end of an
        ENERGY_FORCE calculation is the PRINT setting is on.
        """
        def wrapper(parser):

            end_str = " SUM OF ATOMIC FORCES"
            end = False
            force_array = []

            # Loop through coordinates until the sum of forces is read
            while not end:
                line = parser.fIn.readline()
                if line.startswith(end_str):
                    end = True
                else:
                    forces = line.split()[-3:]
                    forces = [float(x) for x in forces]
                    force_array.append(forces)
            force_array = np.array(force_array)

            # If anything found, push the results to the correct section
            if len(force_array) != 0:
                parser.backend.addArrayValues("atom_forces", force_array, unit="forceAu")

        return wrapper

    def adHoc_single_point_converged(self):
        """Called when the SCF cycle of a single point calculation has converged.
        """
        def wrapper(parser):
            parser.backend.addValue("single_configuration_calculation_converged", True)
        return wrapper

    def adHoc_single_point_not_converged(self):
        """Called when the SCF cycle of a single point calculation did not converge.
        """
        def wrapper(parser):
            parser.backend.addValue("single_configuration_calculation_converged", False)
        return wrapper





    # def adHoc_cp2k_section_cell(self):
        # """Used to extract the cell information.
        # """
        # def wrapper(parser):
            # # Read the lines containing the cell vectors
            # a_line = parser.fIn.readline()
            # b_line = parser.fIn.readline()
            # c_line = parser.fIn.readline()

            # # Define the regex that extracts the components and apply it to the lines
            # regex_string = r" CELL\| Vector \w \[angstrom\]:\s+({0})\s+({0})\s+({0})".format(cm.regex_f)
            # regex_compiled = re.compile(regex_string)
            # a_result = regex_compiled.match(a_line)
            # b_result = regex_compiled.match(b_line)
            # c_result = regex_compiled.match(c_line)

            # # Convert the string results into a 3x3 numpy array
            # cell = np.zeros((3, 3))
            # cell[0, :] = [float(x) for x in a_result.groups()]
            # cell[1, :] = [float(x) for x in b_result.groups()]
            # cell[2, :] = [float(x) for x in c_result.groups()]

            # # Push the results to the correct section
            # parser.backend.addArrayValues("simulation_cell", cell, unit="angstrom")

        # return wrapper

    # def onClose_cp2k_section_filenames(self, backend, gIndex, section):
        # """
        # """
        # # If the input file is available, parse it
        # input_file = section["cp2k_input_filename"][0]
        # filepath = self.file_service.get_absolute_path_to_file(input_file)
        # if filepath is not None:
            # input_parser = CP2KInputParser(filepath, self.parser_context)
            # input_parser.parse()
        # else:
            # logger.warning("The input file of the calculation could not be found.")

    # def onClose_cp2k_section_md_coordinate_atom(self, backend, gIndex, section):
        # """Given the string with the coordinate components for one atom, make it
        # into a numpy array of coordinate components and store for later
        # concatenation.
        # """
        # force_string = section["cp2k_md_coordinate_atom_string"][0]
        # components = np.array([float(x) for x in force_string.split()])
        # backend.addArrayValues("cp2k_md_coordinate_atom_float", components)

    # def onClose_cp2k_section_md_coordinates(self, backend, gIndex, section):
        # """When all the coordinates for individual atoms have been gathered,
        # concatenate them into one big array and forward to the backend.
        # """
        # forces = section["cp2k_md_coordinate_atom_float"]
        # forces = np.array(forces)
        # backend.addArrayValues("cp2k_md_coordinates", forces)

    # def onClose_cp2k_section_md_force_atom(self, backend, gIndex, section):
        # """Given the string with the force components for one atom, make it
        # into a numpy array of force components and store for later
        # concatenation.
        # """
        # force_string = section["cp2k_md_force_atom_string"][0]
        # components = np.array([float(x) for x in force_string.split()])
        # backend.addArrayValues("cp2k_md_force_atom_float", components)

    # def onClose_cp2k_section_md_forces(self, backend, gIndex, section):
        # """When all the forces for individual atoms have been gathered,
        # concatenate them into one big array and forward to the backend.
        # """
        # forces = section["cp2k_md_force_atom_float"]
        # forces = np.array(forces)
        # backend.addArrayValues("cp2k_md_forces", forces, unit="forceAu")


    #===========================================================================
    # The functions that trigger when sections are closed
    # def onClose_section_method(self, backend, gIndex, section):
        # """When all the functional definitions have been gathered, matches them
        # with the nomad correspondents and combines into one single string which
        # is put into the backend.
        # """
        # # Transform the CP2K self-interaction correction string to the NOMAD
        # # correspondent, and push directly to the superBackend to avoid caching
        # sic_cp2k = section["self_interaction_correction_method"][0]
        # sic_map = {
            # "NO": "",
            # "AD SIC": "SIC_AD",
            # "Explicit Orbital SIC": "SIC_EXPLICIT_ORBITALS",
            # "SPZ/MAURI SIC": "SIC_MAURI_SPZ",
            # "US/MAURI SIC": "SIC_MAURI_US",
        # }
        # sic_nomad = sic_map.get(sic_cp2k)
        # if sic_nomad is not None:
            # backend.superBackend.addValue('self_interaction_correction_method', sic_nomad)
        # else:
            # logger.warning("Unknown self-interaction correction method used.")