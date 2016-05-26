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
        self.cache_service = parser_context.cache_service
        self.regex_f = "-?\d+\.\d+(?:E(?:\+|-)\d+)?"  # Regex for a floating point value
        self.regex_i = "-?\d+"  # Regex for an integer
        self.regex_word = "[^\s]+"  # Regex for a single word. Can contain anything else but whitespace
        self.section_method_index = None
        self.section_system_index = None
        self.forces = None

        #=======================================================================
        # Cache levels
        self.caching_levels = {
            'x_cp2k_atoms': CachingLevel.ForwardAndCache,
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

        #=======================================================================
        # Cached values
        self.cache_service.add_cache_object("simulation_cell", single=False, update=False)
        self.cache_service.add_cache_object("number_of_scf_iterations", 0)
        self.cache_service.add_cache_object("atom_positions", single=False, update=True)
        self.cache_service.add_cache_object("atom_labels", single=False, update=False)
        self.cache_service.add_cache_object("number_of_atoms", single=False, update=False)

    #===========================================================================
    # SimpleMatchers

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
                    adHoc=self.adHoc_x_cp2k_section_cell(),
                    otherMetaInfo=["simulation_cell"]
                ),
                SM( " DFT\|",
                    otherMetaInfo=["self_interaction_correction_method"],
                    forwardMatch=True,
                    subMatchers=[
                        SM( " DFT\| Multiplicity\s+(?P<spin_target_multiplicity>{})".format(self.regex_i)),
                        SM( " DFT\| Charge\s+(?P<total_charge>{})".format(self.regex_i)),
                        SM( " DFT\| Self-interaction correction \(SIC\)\s+(?P<self_interaction_correction_method>[^\n]+)"),
                    ]
                ),
                SM( "  Total number of",
                    forwardMatch=True,
                    sections=["x_cp2k_section_total_numbers"],
                    subMatchers=[
                        SM( "  Total number of            - Atomic kinds:\s+(?P<x_cp2k_atomic_kinds>\d+)"),
                        SM( "\s+- Atoms:\s+(?P<x_cp2k_atoms>\d+)",
                            otherMetaInfo=["number_of_atoms"],
                        ),
                        SM( "\s+- Shell sets:\s+(?P<x_cp2k_shell_sets>\d+)"),
                        SM( "\s+- Shells:\s+(?P<x_cp2k_shells>\d+)"),
                        SM( "\s+- Primitive Cartesian functions:\s+(?P<x_cp2k_primitive_cartesian_functions>\d+)"),
                        SM( "\s+- Cartesian basis functions:\s+(?P<x_cp2k_cartesian_basis_functions>\d+)"),
                        SM( "\s+- Spherical basis functions:\s+(?P<x_cp2k_spherical_basis_functions>\d+)"),
                    ]
                ),
                SM( " Maximum angular momentum of",
                    forwardMatch=True,
                    sections=["x_cp2k_section_maximum_angular_momentum"],
                    subMatchers=[
                        SM( "  Maximum angular momentum of- Orbital basis functions::\s+(?P<x_cp2k_orbital_basis_functions>\d+)"),
                        SM( "\s+- Local part of the GTH pseudopotential:\s+(?P<x_cp2k_local_part_of_gth_pseudopotential>\d+)"),
                        SM( "\s+- Non-local part of the GTH pseudopotential:\s+(?P<x_cp2k_non_local_part_of_gth_pseudopotential>\d+)"),
                    ]
                )
            ]
        )

    # SimpleMatcher for an SCF wavefunction optimization
    def scf(self):
        return SM( " SCF WAVEFUNCTION OPTIMIZATION",
            subMatchers=[
                SM( r"  Trace\(PS\):",
                    sections=["section_scf_iteration"],
                    repeats=True,
                    subMatchers=[
                        SM( r"  Exchange-correlation energy:\s+(?P<energy_XC_scf_iteration__hartree>{})".format(self.regex_f)),
                        SM( r"\s+\d+\s+\S+\s+{0}\s+{0}\s+{0}\s+(?P<energy_total_scf_iteration__hartree>{0})\s+(?P<energy_change_scf_iteration__hartree>{0})".format(self.regex_f)),
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
                SM( r"  Electronic kinetic energy:\s+(?P<electronic_kinetic_energy__hartree>{})".format(self.regex_f)),
                SM( r" **************************** NUMERICAL STRESS ********************************".replace("*", "\*"),
                    adHoc=self.adHoc_stress_calculation(),
                ),
                SM( r" ENERGY\| Total FORCE_EVAL \( \w+ \) energy \(a\.u\.\):\s+(?P<energy_total__hartree>{0})".format(self.regex_f)),
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
                        SM( "  1/3 Trace\(stress tensor\):\s+(?P<x_cp2k_stress_tensor_one_third_of_trace__GPa>{})".format(self.regex_f)),
                        SM( "  Det\(stress tensor\)\s+:\s+(?P<x_cp2k_stress_tensor_determinant__GPa3>{})".format(self.regex_f)),
                        SM( " EIGENVECTORS AND EIGENVALUES OF THE STRESS TENSOR",
                            adHoc=self.adHoc_stress_tensor_eigenpairs()),
                    ]
                )
            ]
        )

    # SimpleMatcher for an SCF wavefunction optimization
    def quickstep(self):
        return SM(
            " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
            forwardMatch=True,
            subMatchers=[
                SM( " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
                    adHoc=self.adHoc_x_cp2k_section_quickstep_atom_information(),
                    otherMetaInfo=["atom_labels", "atom_positions"]
                )
            ]
        )

    #===========================================================================
    # onClose triggers
    def onClose_section_scf_iteration(self, backend, gIndex, section):
        """Keep track of how many SCF iteration are made."""
        self.cache_service["number_of_scf_iterations"] += 1

    def onClose_x_cp2k_section_total_numbers(self, backend, gIndex, section):
        """Keep track of how many SCF iteration are made."""
        number_of_atoms = section["x_cp2k_atoms"][0]
        self.cache_service["number_of_atoms"] = number_of_atoms

    def onClose_section_run(self, backend, gIndex, section):
        """Information that is pushed regardless at the end of parsing.
        Contains also information that is totally agnostic on the calculation
        contents, like program_basis_set_type.
        """
        backend.addValue("program_basis_set_type", "gaussian")

    def onClose_section_method(self, backend, gIndex, section):
        """When all the functional definitions have been gathered, matches them
        with the nomad correspondents and combines into one single string which
        is put into the backend.
        """
        self.section_method_index = gIndex

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

    def onClose_section_system(self, backend, gIndex, section):
        """Stores the index of the section method. Should always be 0, but
        let's get it dynamically just in case there's something wrong.
        """
        self.section_system_index = gIndex
        if self.forces is not None:
            backend.addArrayValues("atom_forces", self.forces, unit="forceAu")
        self.forces = None
        self.cache_service.push_value("number_of_atoms")
        self.cache_service.push_array_values("simulation_cell", unit="angstrom")
        self.cache_service.push_array_values("configuration_periodic_dimensions")
        self.cache_service.push_array_values("atom_positions", unit="angstrom")
        self.cache_service.push_array_values("atom_labels")

    def onClose_section_single_configuration_calculation(self, backend, gIndex, section):
        """
        """
        # Write the references to section_method and section_system
        backend.addValue('single_configuration_to_calculation_method_ref', self.section_method_index)
        backend.addValue('single_configuration_calculation_to_system_ref', self.section_system_index)

    #===========================================================================
    # adHoc functions
    def adHoc_x_cp2k_section_cell(self):
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

            # Push the results to cache
            self.cache_service["simulation_cell"] = cell
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
                self.forces = force_array

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

    def adHoc_x_cp2k_section_quickstep_atom_information(self):
        """Used to extract the initial atomic coordinates and names in the
        Quickstep module.
        """
        def wrapper(parser):

            # Define the regex that extracts the information
            regex_string = r"\s+\d+\s+\d+\s+(\w+)\s+\d+\s+({0})\s+({0})\s+({0})".format(self.regex_f)
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
                self.cache_service["atom_positions"] = coordinates
                self.cache_service["atom_labels"] = labels

        return wrapper

    #===========================================================================
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
