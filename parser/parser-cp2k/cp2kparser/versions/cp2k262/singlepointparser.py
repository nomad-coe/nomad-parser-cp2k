import re
from nomadcore.simple_parser import SimpleMatcher as SM
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
        self.section_system_index = None

        # Simple matcher for run type ENERGY_FORCE, ENERGY with QUICKSTEP
        self.energy_force = SM(
            " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
            forwardMatch=True,
            subMatchers=[
                SM( " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
                    adHoc=self.adHoc_cp2k_section_quickstep_atom_information(),
                    otherMetaInfo=["atom_labels", "atom_positions"]
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
                            otherMetaInfo=["single_configuration_calculation_converged"],
                            adHoc=self.adHoc_single_point_converged()
                        ),
                        SM( r"  \*\*\* SCF run NOT converged \*\*\*",
                            otherMetaInfo=["single_configuration_calculation_converged"],
                            adHoc=self.adHoc_single_point_not_converged()
                        ),
                        SM( r"  Electronic kinetic energy:\s+(?P<electronic_kinetic_energy__hartree>{})".format(self.cm.regex_f)),
                        SM( r" **************************** NUMERICAL STRESS ********************************".replace("*", "\*"),
                            adHoc=self.adHoc_stress_calculation(),
                        ),
                        SM( r" ENERGY\| Total FORCE_EVAL \( \w+ \) energy \(a\.u\.\):\s+(?P<energy_total__hartree>{0})".format(self.cm.regex_f)),
                        SM( r" ATOMIC FORCES in \[a\.u\.\]"),
                        SM( r" # Atom   Kind   Element          X              Y              Z",
                            adHoc=self.adHoc_atom_forces(),
                            otherMetaInfo=["atom_forces"],
                        ),
                        SM( r" (?:NUMERICAL )?STRESS TENSOR \[GPa\]",
                            sections=["section_stress_tensor"],
                            otherMetaInfo=["stress_tensor"],
                            subMatchers=[
                                SM( r"\s+X\s+Y\s+Z",
                                    adHoc=self.adHoc_stress_tensor()
                                ),
                                SM( "  1/3 Trace\(stress tensor\):\s+(?P<x_cp2k_stress_tensor_one_third_of_trace__GPa>{})".format(self.cm.regex_f)),
                                SM( "  Det\(stress tensor\)\s+:\s+(?P<x_cp2k_stress_tensor_determinant__GPa3>{})".format(self.cm.regex_f)),
                                SM( " EIGENVECTORS AND EIGENVALUES OF THE STRESS TENSOR",
                                    adHoc=self.adHoc_stress_tensor_eigenpairs()),
                            ]
                        )
                    ]
                )
            ]
        )

        # Compose root matcher according to the run type. This way the
        # unnecessary regex parsers will not be compiled and searched. Saves
        # computational time.
        self.root_matcher = SM("",
            forwardMatch=True,
            sections=['section_run', "section_single_configuration_calculation", "section_system", "section_method"],
            otherMetaInfo=["atom_forces"],
            subMatchers=[
                self.cm.header(),
                self.energy_force
            ]
        )
        #=======================================================================
        # The cache settings
        self.caching_level_for_metaname = self.cm.caching_levels

        #=======================================================================
        # The additional onClose trigger functions
        self.onClose = self.cm.getOnCloseTriggers()

    #===========================================================================
    # onClose triggers. These are specific to this main parser, common
    # triggers are imprted from commonmatchers module.
    def onClose_section_scf_iteration(self, backend, gIndex, section):
        """Keep track of how many SCF iteration are made."""
        self.scf_iterations += 1

    def onClose_section_system(self, backend, gIndex, section):
        """Stores the index of the section method. Should always be 0, but
        let's get it dynamically just in case there's something wrong.
        """
        self.section_system_index = gIndex

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
        backend.addValue("number_of_scf_iterations", self.scf_iterations)

        # Write the references to section_method and section_system
        backend.addValue('single_configuration_to_calculation_method_ref', self.section_method_index)
        backend.addValue('single_configuration_calculation_to_system_ref', self.section_system_index)

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
                parser.backend.addArrayValues("atom_positions", coordinates, unit="angstrom")
                parser.backend.addArrayValues("atom_labels", labels)

        return wrapper

    def adHoc_atom_forces(self):
        """Used to extract the final atomic forces printed at the end of a
        calculation.
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

    def adHoc_stress_tensor(self):
        """Used to extract the stress tensor printed at the end of a
        calculation.
        """
        def wrapper(parser):
            row1 = [float(x) for x in parser.fIn.readline().split()[-3:]]
            row2 = [float(x) for x in parser.fIn.readline().split()[-3:]]
            row3 = [float(x) for x in parser.fIn.readline().split()[-3:]]
            stress_array = np.array([row1, row2, row3])
            parser.backend.addArrayValues("stress_tensor", stress_array, unit="GPa")

        return wrapper

    def adHoc_stress_tensor_eigenpairs(self):
        """Parses the stress tensor eigenpairs.
        """
        def wrapper(parser):
            parser.fIn.readline()
            eigenvalues = np.array([float(x) for x in parser.fIn.readline().split()][::-1])
            parser.fIn.readline()
            row1 = [float(x) for x in parser.fIn.readline().split()]
            row2 = [float(x) for x in parser.fIn.readline().split()]
            row3 = [float(x) for x in parser.fIn.readline().split()]
            eigenvectors = np.fliplr(np.array([row1, row2, row3]))
            parser.backend.addArrayValues("x_cp2k_stress_tensor_eigenvalues", eigenvalues, unit="GPa")
            parser.backend.addArrayValues("x_cp2k_stress_tensor_eigenvectors", eigenvectors)
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

    def adHoc_stress_calculation(self):
        """Used to skip over the stress tensor calculation details.
        """
        def wrapper(parser):
            end_line = " **************************** NUMERICAL STRESS END *****************************\n"
            finished = False
            while not finished:
                line = parser.fIn.readline()
                if line == end_line:
                    finished = True
        return wrapper
