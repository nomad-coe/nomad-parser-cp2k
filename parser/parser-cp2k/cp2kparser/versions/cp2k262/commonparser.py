from __future__ import absolute_import
from builtins import str
import re
import numpy as np
import logging
from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.caching_backend import CachingLevel
from nomadcore.unit_conversion.unit_conversion import convert_unit
from nomadcore.baseclasses import CommonParser
from .inputparser import CP2KInputParser
logger = logging.getLogger("nomad")


#===============================================================================
class CP2KCommonParser(CommonParser):
    """
    This class is used to store and instantiate common parts of the
    hierarchical SimpleMatcher structure used in the parsing of a CP2K
    output file.
    """
    def __init__(self, parser_context):
        super(CP2KCommonParser, self).__init__(parser_context)
        self.section_method_index = None
        self.section_system_index = None
        self.test_electronic_structure_method = "DFT"
        self.basis_to_kind_mapping = []

        #=======================================================================
        # Cache levels
        self.caching_levels = {
            'x_cp2k_atoms': CachingLevel.ForwardAndCache,
            'section_XC_functionals': CachingLevel.ForwardAndCache,
            'self_interaction_correction_method': CachingLevel.Cache,
            'x_cp2k_section_program_information': CachingLevel.ForwardAndCache,
            'x_cp2k_section_quickstep_settings': CachingLevel.ForwardAndCache,
            'x_cp2k_section_atomic_kind': CachingLevel.ForwardAndCache,
            'x_cp2k_section_kind_basis_set': CachingLevel.ForwardAndCache,
        }

        #=======================================================================
        # Globally cached values
        self.cache_service.add("simulation_cell", single=False, update=False)
        self.cache_service.add("number_of_scf_iterations", 0)
        self.cache_service.add("atom_positions", single=False, update=True)
        self.cache_service.add("atom_labels", single=False, update=False)
        self.cache_service.add("number_of_atoms", single=False, update=False)

    #===========================================================================
    # SimpleMatchers

    # SimpleMatcher for the header that is common to all run types
    def header(self):
        return SM( " DBCSR\| Multiplication driver",
            forwardMatch=True,
            subMatchers=[
                SM( " DBCSR\| Multiplication driver",
                    forwardMatch=True,
                    sections=['x_cp2k_section_dbcsr'],
                    subMatchers=[
                        SM( " DBCSR\| Multiplication driver\s+(?P<x_cp2k_dbcsr_multiplication_driver>{})".format(self.regexs.regex_word)),
                        SM( " DBCSR\| Multrec recursion limit\s+(?P<x_cp2k_dbcsr_multrec_recursion_limit>{})".format(self.regexs.regex_i)),
                        SM( " DBCSR\| Multiplication stack size\s+(?P<x_cp2k_dbcsr_multiplication_stack_size>{})".format(self.regexs.regex_i)),
                        SM( " DBCSR\| Multiplication size stacks\s+(?P<x_cp2k_dbcsr_multiplication_size_stacks>{})".format(self.regexs.regex_i)),
                        SM( " DBCSR\| Use subcommunicators\s+(?P<x_cp2k_dbcsr_use_subcommunicators>{})".format(self.regexs.regex_letter)),
                        SM( " DBCSR\| Use MPI combined types\s+(?P<x_cp2k_dbcsr_use_mpi_combined_types>{})".format(self.regexs.regex_letter)),
                        SM( " DBCSR\| Use MPI memory allocation\s+(?P<x_cp2k_dbcsr_use_mpi_memory_allocation>{})".format(self.regexs.regex_letter)),
                        SM( " DBCSR\| Use Communication thread\s+(?P<x_cp2k_dbcsr_use_communication_thread>{})".format(self.regexs.regex_letter)),
                        SM( " DBCSR\| Communication thread load\s+(?P<x_cp2k_dbcsr_communication_thread_load>{})".format(self.regexs.regex_i)),
                    ]
                ),
                SM( "  **** **** ******  **  PROGRAM STARTED AT".replace("*", "\*"),
                    forwardMatch=True,
                    sections=['x_cp2k_section_startinformation'],
                    subMatchers=[
                        SM( "  **** **** ******  **  PROGRAM STARTED AT\s+(?P<x_cp2k_start_time>{})".replace("*", "\*").format(self.regexs.regex_eol)),
                        SM( " ***** ** ***  *** **   PROGRAM STARTED ON\s+(?P<x_cp2k_start_host>{})".replace("*", "\*").format(self.regexs.regex_word)),
                        SM( " **    ****   ******    PROGRAM STARTED BY\s+(?P<x_cp2k_start_user>{})".replace("*", "\*").format(self.regexs.regex_word)),
                        SM( " ***** **    ** ** **   PROGRAM PROCESS ID\s+(?P<x_cp2k_start_id>{})".replace("*", "\*").format(self.regexs.regex_i)),
                        SM( "  **** **  *******  **  PROGRAM STARTED IN".replace("*", "\*"),
                            forwardMatch=True,
                            adHoc=self.adHoc_run_dir(),
                        )
                    ]
                ),
                SM( " CP2K\| version string:",
                    sections=['x_cp2k_section_program_information'],
                    forwardMatch=True,
                    subMatchers=[
                        SM( " CP2K\| version string:\s+(?P<program_version>{})".format(self.regexs.regex_eol)),
                        SM( " CP2K\| source code revision number:\s+svn:(?P<x_cp2k_svn_revision>\d+)"),
                        SM( " CP2K\| is freely available from{}".format(self.regexs.regex_eol)),
                        SM( " CP2K\| Program compiled at\s+(?P<x_cp2k_program_compilation_datetime>{})".format(self.regexs.regex_eol)),
                        SM( " CP2K\| Program compiled on\s+(?P<program_compilation_host>{})".format(self.regexs.regex_eol)),
                        SM( " CP2K\| Program compiled for{}".format(self.regexs.regex_eol)),
                        SM( " CP2K\| Input file name\s+(?P<x_cp2k_input_filename>{})".format(self.regexs.regex_eol)),
                    ]
                ),
                SM( " GLOBAL\|",
                    sections=['x_cp2k_section_global_settings'],
                    subMatchers=[
                        SM( " GLOBAL\| Force Environment number"),
                        SM( " GLOBAL\| Basis set file name\s+(?P<x_cp2k_basis_set_filename>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| Geminal file name\s+(?P<x_cp2k_geminal_filename>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| Potential file name\s+(?P<x_cp2k_potential_filename>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| MM Potential file name\s+(?P<x_cp2k_mm_potential_filename>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| Coordinate file name\s+(?P<x_cp2k_coordinate_filename>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| Method name\s+(?P<x_cp2k_method_name>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| Project name"),
                        SM( " GLOBAL\| Preferred FFT library\s+(?P<x_cp2k_preferred_fft_library>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| Preferred diagonalization lib.\s+(?P<x_cp2k_preferred_diagonalization_library>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| Run type\s+(?P<x_cp2k_run_type>{})".format(self.regexs.regex_eol)),
                        SM( " GLOBAL\| All-to-all communication in single precision"),
                        SM( " GLOBAL\| FFTs using library dependent lengths"),
                        SM( " GLOBAL\| Global print level"),
                        SM( " GLOBAL\| Total number of message passing processes"),
                        SM( " GLOBAL\| Number of threads for this process"),
                        SM( " GLOBAL\| This output is from process"),
                    ],
                    otherMetaInfo=[
                        "section_XC_functionals",
                        'XC_functional_name',
                        'XC_functional_weight',
                        'XC_functional',
                        'configuration_periodic_dimensions',
                        "stress_tensor_method",
                        "atom_positions",
                    ],
                ),
                SM( " CELL\|",
                    adHoc=self.adHoc_x_cp2k_section_cell(),
                    otherMetaInfo=["simulation_cell"]
                ),
            ]
        )

    # SimpleMatcher for an SCF wavefunction optimization
    def quickstep_calculation(self):
        return SM( " SCF WAVEFUNCTION OPTIMIZATION",
            sections=["x_cp2k_section_quickstep_calculation"],
            subMatchers=[
                SM( r"  Trace\(PS\):",
                    sections=["x_cp2k_section_scf_iteration"],
                    repeats=True,
                    subMatchers=[
                        SM( r"  Exchange-correlation energy:\s+(?P<x_cp2k_energy_XC_scf_iteration__hartree>{})".format(self.regexs.regex_f)),
                        SM( r"\s+\d+\s+\S+\s+{0}\s+{0}\s+{0}\s+(?P<x_cp2k_energy_total_scf_iteration__hartree>{0})\s+(?P<x_cp2k_energy_change_scf_iteration__hartree>{0})".format(self.regexs.regex_f)),
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
                SM( r"  Electronic kinetic energy:\s+(?P<x_cp2k_electronic_kinetic_energy__hartree>{})".format(self.regexs.regex_f)),
                SM( r" **************************** NUMERICAL STRESS ********************************".replace("*", "\*"),
                    # endReStr=" **************************** NUMERICAL STRESS END *****************************".replace("*", "\*"),
                    adHoc=self.adHoc_stress_calculation(),
                ),
                SM( r" ENERGY\| Total FORCE_EVAL \( \w+ \) energy \(a\.u\.\):\s+(?P<x_cp2k_energy_total__hartree>{0})".format(self.regexs.regex_f),
                    otherMetaInfo=["energy_total"],
                ),
                SM( r" ATOMIC FORCES in \[a\.u\.\]"),
                SM( r" # Atom   Kind   Element          X              Y              Z",
                    adHoc=self.adHoc_atom_forces(),
                    otherMetaInfo=["atom_forces", "x_cp2k_atom_forces"],
                ),
                SM( r" (?:NUMERICAL )?STRESS TENSOR \[GPa\]",
                    sections=["x_cp2k_section_stress_tensor"],
                    subMatchers=[
                        SM( r"\s+X\s+Y\s+Z",
                            adHoc=self.adHoc_stress_tensor(),
                            otherMetaInfo=["stress_tensor", "section_stress_tensor"],
                        ),
                        SM( "  1/3 Trace\(stress tensor\):\s+(?P<x_cp2k_stress_tensor_one_third_of_trace__GPa>{})".format(self.regexs.regex_f)),
                        SM( "  Det\(stress tensor\)\s+:\s+(?P<x_cp2k_stress_tensor_determinant__GPa3>{})".format(self.regexs.regex_f)),
                        SM( " EIGENVECTORS AND EIGENVALUES OF THE STRESS TENSOR",
                            adHoc=self.adHoc_stress_tensor_eigenpairs()),
                    ]
                )
            ]
        )

    # SimpleMatcher the stuff that is done to initialize a quickstep calculation
    def quickstep_header(self):
        return SM( " *******************************************************************************".replace("*", "\*"),
            forwardMatch=True,
            sections=["x_cp2k_section_quickstep_settings"],
            subMatchers=[
                SM( " DFT\|",
                    forwardMatch=True,
                    subMatchers=[
                        SM( " DFT\| Spin restricted Kohn-Sham (RKS) calculation\s+(?P<x_cp2k_spin_restriction>{})".format(self.regexs.regex_word)),
                        SM( " DFT\| Multiplicity\s+(?P<spin_target_multiplicity>{})".format(self.regexs.regex_i)),
                        SM( " DFT\| Number of spin states\s+(?P<number_of_spin_channels>{})".format(self.regexs.regex_i)),
                        SM( " DFT\| Charge\s+(?P<total_charge>{})".format(self.regexs.regex_i)),
                        SM( " DFT\| Self-interaction correction \(SIC\)\s+(?P<self_interaction_correction_method>[^\n]+)"),
                    ],
                    otherMetaInfo=["self_interaction_correction_method"],
                ),
                SM( " DFT\+U\|",
                    adHoc=self.adHoc_dft_plus_u(),
                ),
                SM( " QS\|",
                    forwardMatch=True,
                    subMatchers=[
                        SM( " QS\| Method:\s+(?P<x_cp2k_quickstep_method>{})".format(self.regexs.regex_word)),
                        SM( " QS\| Density plane wave grid type\s+{}".format(self.regexs.regex_eol)),
                        SM( " QS\| Number of grid levels:\s+{}".format(self.regexs.regex_i)),
                        SM( " QS\| Density cutoff \[a\.u\.\]:\s+(?P<x_cp2k_planewave_cutoff>{})".format(self.regexs.regex_f)),
                        SM( " QS\| Multi grid cutoff \[a\.u\.\]: 1\) grid level\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                           2\) grid level\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                           3\) grid level\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                           4\) grid level\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\| Grid level progression factor:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\| Relative density cutoff \[a\.u\.\]:".format(self.regexs.regex_f)),
                        SM( " QS\| Consistent realspace mapping and integration"),
                        SM( " QS\| Interaction thresholds: eps_pgf_orb:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                         eps_filter_matrix:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                         eps_core_charge:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                         eps_rho_gspace:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                         eps_rho_rspace:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                         eps_gvg_rspace:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                         eps_ppl:\s+{}".format(self.regexs.regex_f)),
                        SM( " QS\|                         eps_ppnl:\s+{}".format(self.regexs.regex_f)),
                    ],
                ),
                SM( " ATOMIC KIND INFORMATION",
                    sections=["x_cp2k_section_atomic_kinds", "section_method_basis_set"],
                    subMatchers=[
                        SM( "\s+(?P<x_cp2k_kind_number>{0})\. Atomic kind: (?P<x_cp2k_kind_element_symbol>{1})\s+Number of atoms:\s+(?P<x_cp2k_kind_number_of_atoms>{1})".format(self.regexs.regex_i, self.regexs.regex_word),
                            repeats=True,
                            sections=["x_cp2k_section_atomic_kind", "x_cp2k_section_kind_basis_set"],
                            subMatchers=[
                                SM( "     Orbital Basis Set\s+(?P<x_cp2k_kind_basis_set_name>{})".format(self.regexs.regex_word)),
                                SM( "       Number of orbital shell sets:\s+(?P<x_cp2k_basis_set_number_of_orbital_shell_sets>{})".format(self.regexs.regex_i)),
                                SM( "       Number of orbital shells:\s+(?P<x_cp2k_basis_set_number_of_orbital_shells>{})".format(self.regexs.regex_i)),
                                SM( "       Number of primitive Cartesian functions:\s+(?P<x_cp2k_basis_set_number_of_primitive_cartesian_functions>{})".format(self.regexs.regex_i)),
                                SM( "       Number of Cartesian basis functions:\s+(?P<x_cp2k_basis_set_number_of_cartesian_basis_functions>{})".format(self.regexs.regex_i)),
                                SM( "       Number of spherical basis functions:\s+(?P<x_cp2k_basis_set_number_of_spherical_basis_functions>{})".format(self.regexs.regex_i)),
                                SM( "       Norm type:\s+(?P<x_cp2k_basis_set_norm_type>{})".format(self.regexs.regex_i)),
                            ]
                        )
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
                ),
                SM( " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
                    forwardMatch=True,
                    subMatchers=[
                        SM( " MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
                            adHoc=self.adHoc_x_cp2k_section_quickstep_atom_information(),
                            otherMetaInfo=["atom_labels", "atom_positions"]
                        )
                    ]
                ),
                SM( " SCF PARAMETERS",
                    forwardMatch=True,
                    subMatchers=[
                        SM( " SCF PARAMETERS         Density guess:\s+{}".format(self.regexs.regex_eol)),
                        SM( "                        max_scf:\s+(?P<scf_max_iteration>{})".format(self.regexs.regex_i)),
                        SM( "                        max_scf_history:\s+{}".format(self.regexs.regex_i)),
                        SM( "                        max_diis:\s+{}".format(self.regexs.regex_i)),
                        SM( "                        eps_scf:\s+(?P<scf_threshold_energy_change__hartree>{})".format(self.regexs.regex_f)),
                    ]
                ),
                SM( " MP2\|",
                    adHoc=self.adHoc_mp2()
                ),
                SM( " RI-RPA\|",
                    adHoc=self.adHoc_rpa()
                ),
            ]
        )

    #===========================================================================
    # onClose triggers
    def onClose_x_cp2k_section_total_numbers(self, backend, gIndex, section):
        """Keep track of how many SCF iteration are made."""
        number_of_atoms = section.get_latest_value("x_cp2k_atoms")
        if number_of_atoms is not None:
            self.cache_service["number_of_atoms"] = number_of_atoms

    # def onClose_x_cp2k_section_quickstep_calculation(self, backend, gIndex, section):
        # print "quickstep CLOSED"

    # def onClose_x_cp2k_section_geometry_optimization_step(self, backend, gIndex, section):
        # print "Optimisation step CLOSED"

    def onClose_section_method(self, backend, gIndex, section):
        """When all the functional definitions have been gathered, matches them
        with the nomad correspondents and combines into one single string which
        is put into the backend.
        """
        self.section_method_index = gIndex

        # Transform the CP2K self-interaction correction string to the NOMAD
        # correspondent, and push directly to the superBackend to avoid caching
        try:
            sic_cp2k = section.get_latest_value("self_interaction_correction_method")
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

    def onClose_section_run(self, backend, gIndex, section):
        backend.addValue("program_name", "CP2K")

    def onClose_x_cp2k_section_quickstep_settings(self, backend, gIndex, section):
        backend.addValue("program_basis_set_type", "gaussian")
        backend.addValue("electronic_structure_method", self.test_electronic_structure_method)

        # See if the cutoff is available
        cutoff = section.get_latest_value("x_cp2k_planewave_cutoff")
        if cutoff is not None:
            gid = backend.openSection("section_basis_set_cell_dependent")
            cutoff = convert_unit(2*cutoff, "hartree")
            backend.addValue("basis_set_planewave_cutoff", cutoff)
            backend.closeSection("section_basis_set_cell_dependent", gid)

    def onClose_section_method_basis_set(self, backend, gIndex, section):
        backend.addValue("method_basis_set_kind", "wavefunction")
        backend.addValue("number_of_basis_sets_atom_centered", len(self.basis_to_kind_mapping))
        backend.addArrayValues("mapping_section_method_basis_set_atom_centered", np.array(self.basis_to_kind_mapping))

    def onClose_x_cp2k_section_atomic_kind(self, backend, gIndex, section):
        kindID = backend.openSection("section_method_atom_kind")
        basisID = backend.openSection("section_basis_set_atom_centered")

        element_symbol = section.get_latest_value("x_cp2k_kind_element_symbol")
        kind_number = section.get_latest_value("x_cp2k_kind_number")
        basis_set_name = section.get_latest_value(["x_cp2k_section_kind_basis_set", "x_cp2k_kind_basis_set_name"])
        atom_number = self.get_atomic_number(element_symbol)
        kind_label = element_symbol + str(kind_number)
        backend.addValue("method_atom_kind_atom_number", atom_number)
        backend.addValue("method_atom_kind_label", kind_label)
        backend.addValue("basis_set_atom_number", atom_number)
        backend.addValue("basis_set_atom_centered_short_name", basis_set_name)

        # Add the reference based mapping between basis and atomic kind
        self.basis_to_kind_mapping.append([basisID, kindID])

        backend.closeSection("section_basis_set_atom_centered", basisID)
        backend.closeSection("section_method_atom_kind", kindID)

    def onClose_x_cp2k_section_program_information(self, backend, gIndex, section):
        input_file = section.get_latest_value("x_cp2k_input_filename")
        self.file_service.set_file_id(input_file, "input")

    def onClose_x_cp2k_section_global_settings(self, backend, gIndex, section):
        # If the input file is available, parse it
        filepath = self.file_service.get_file_by_id("input")
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
        self.cache_service.push_value("number_of_atoms")
        # self.cache_service.push_array_values("simulation_cell", unit="angstrom")
        self.cache_service.push_array_values("configuration_periodic_dimensions")
        self.cache_service.push_array_values("atom_labels")

    def onClose_section_single_configuration_calculation(self, backend, gIndex, section):
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
            regex_string = r" CELL\| Vector \w \[angstrom\]:\s+({0})\s+({0})\s+({0})".format(self.regexs.regex_f)
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
                # self.cache_service["atom_forces"] = force_array
                self.backend.addArrayValues("x_cp2k_atom_forces", force_array, unit="forceAu")

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
            parser.backend.addArrayValues("x_cp2k_stress_tensor", stress_array, unit="GPa")

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
            eigenvalues = np.array([float(x) for x in parser.fIn.readline().split()])
            parser.fIn.readline()
            row1 = [float(x) for x in parser.fIn.readline().split()]
            row2 = [float(x) for x in parser.fIn.readline().split()]
            row3 = [float(x) for x in parser.fIn.readline().split()]
            eigenvectors = np.array([row1, row2, row3])
            parser.backend.addArrayValues("x_cp2k_stress_tensor_eigenvalues", eigenvalues, unit="GPa")
            parser.backend.addArrayValues("x_cp2k_stress_tensor_eigenvectors", eigenvectors)
        return wrapper

    def adHoc_single_point_converged(self):
        """Called when the SCF cycle of a single point calculation has converged.
        """
        def wrapper(parser):
            parser.backend.addValue("x_cp2k_quickstep_converged", True)
        return wrapper

    def adHoc_single_point_not_converged(self):
        """Called when the SCF cycle of a single point calculation did not converge.
        """
        def wrapper(parser):
            parser.backend.addValue("x_cp2k_quickstep_converged", False)
        return wrapper

    def adHoc_x_cp2k_section_quickstep_atom_information(self):
        """Used to extract the initial atomic coordinates and names in the
        Quickstep module.
        """
        def wrapper(parser):

            # Define the regex that extracts the information
            regex_string = r"\s+\d+\s+(\d+)\s+(\w+)\s+\d+\s+({0})\s+({0})\s+({0})".format(self.regexs.regex_f)
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
                    label = result.groups()[1] + result.groups()[0]
                    labels.append(label)
                    coordinate = [float(x) for x in result.groups()[2:]]
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

    def adHoc_run_dir(self):
        def wrapper(parser):
            end_str = "\n"
            end = False
            path_array = []

            # Loop through coordinates until the sum of forces is read
            while not end:
                line = parser.fIn.readline()
                if line.startswith(end_str):
                    end = True
                else:
                    path_part = line.split()[-1]
                    path_array.append(path_part)

            # Form the final path and push to backend
            path = "".join(path_array)
            parser.backend.addValue("x_cp2k_start_path", path)

        return wrapper

    def adHoc_dft_plus_u(self):
        def wrapper(parser):
            self.test_electronic_structure_method = "DFT+U"
        return wrapper

    def adHoc_mp2(self):
        def wrapper(parser):
            self.test_electronic_structure_method = "MP2"
        return wrapper

    def adHoc_rpa(self):
        def wrapper(parser):
            self.test_electronic_structure_method = "RPA"
        return wrapper

    # def debug(self):
        # def wrapper(parser):
            # print("FOUND")
        # return wrapper

    #===========================================================================
    # MISC functions
    def get_atomic_number(self, symbol):
        """ Returns the atomic number when given the atomic symbol.

        Args:
            symbol: atomic symbol as string

        Returns:
            The atomic number (number of protons) for the given symbol.
        """
        chemical_symbols = [
            'X',  'H',  'He', 'Li', 'Be',
            'B',  'C',  'N',  'O',  'F',
            'Ne', 'Na', 'Mg', 'Al', 'Si',
            'P',  'S',  'Cl', 'Ar', 'K',
            'Ca', 'Sc', 'Ti', 'V',  'Cr',
            'Mn', 'Fe', 'Co', 'Ni', 'Cu',
            'Zn', 'Ga', 'Ge', 'As', 'Se',
            'Br', 'Kr', 'Rb', 'Sr', 'Y',
            'Zr', 'Nb', 'Mo', 'Tc', 'Ru',
            'Rh', 'Pd', 'Ag', 'Cd', 'In',
            'Sn', 'Sb', 'Te', 'I',  'Xe',
            'Cs', 'Ba', 'La', 'Ce', 'Pr',
            'Nd', 'Pm', 'Sm', 'Eu', 'Gd',
            'Tb', 'Dy', 'Ho', 'Er', 'Tm',
            'Yb', 'Lu', 'Hf', 'Ta', 'W',
            'Re', 'Os', 'Ir', 'Pt', 'Au',
            'Hg', 'Tl', 'Pb', 'Bi', 'Po',
            'At', 'Rn', 'Fr', 'Ra', 'Ac',
            'Th', 'Pa', 'U',  'Np', 'Pu',
            'Am', 'Cm', 'Bk', 'Cf', 'Es',
            'Fm', 'Md', 'No', 'Lr'
        ]

        atomic_numbers = {}
        for Z, name in enumerate(chemical_symbols):
            atomic_numbers[name] = Z

        return atomic_numbers[symbol]
