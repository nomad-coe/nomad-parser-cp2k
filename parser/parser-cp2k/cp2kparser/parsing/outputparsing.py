from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.caching_backend import CachingLevel
import numpy as np


#===============================================================================
class CP2KOutputParser262(object):
    """The object that goes through the CP2K output file and parses everything
    it can using the SimpleParser architecture.
    """

    def __init__(self, cp2kparser, metainfos):
        """Initialize an output parser. The outputparser will sometimes ask the
        CP2KParser for information. E.g. the auxiliary coordinate files are
        identified and read by the CP2KParser.
        """
        self.cp2kparser = cp2kparser
        self.metainfos = metainfos
        self.f_regex = "-?\d+\.\d+(E+|-\d+)?"  # Regex for a floating point value

        # Define the output parsing tree for this version
        self.outputstructure = SM(
            startReStr="",
            sections=['section_run'],
            subMatchers=[
                # SM(
                    # sections=['cp2k_section_dbcsr'],
                    # startReStr=r" DBCSR\| Multiplication driver",
                # ),
                # SM(
                    # sections=['cp2k_section_startinformation'],
                    # startReStr=r"[\*\s]+PROGRAM STARTED AT\s+(?P<cp2k_run_start_date>\d{4}-\d{2}-\d{2}) (?P<cp2k_run_start_time>\d{2}:\d{2}:\d{2}.\d{3})",
                    # forwardMatch=True,
                    # subMatchers=[
                        # SM(
                            # startReStr=r"[\*\s]+PROGRAM STARTED AT\s+(?P<cp2k_run_start_date>\d{4}-\d{2}-\d{2}) (?P<cp2k_run_start_time>\d{2}:\d{2}:\d{2}.\d{3})",
                        # ),
                        # SM(
                            # startReStr=r" CP2K\| version string:\s+(?P<program_version>[\w\d\W\s]+)",
                            # sections=['program_info'],
                        # ),
                        # SM(
                            # startReStr=r" CP2K\| source code revision number:\s+svn:(?P<cp2k_svn_revision>\d+)",
                        # )
                    # ]
                # ),
                SM(
                    sections=["cp2k_section_cell"],
                    startReStr=" CELL\|",
                    forwardMatch=True,
                    subMatchers=[
                        SM(
                            startReStr=" CELL\| Vector a \[angstrom\]:\s+(?P<cp2k_cell_vector_a>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                        ),
                        SM(
                            startReStr=" CELL\| Vector b \[angstrom\]:\s+(?P<cp2k_cell_vector_b>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                        ),
                        SM(
                            startReStr=" CELL\| Vector c \[angstrom\]:\s+(?P<cp2k_cell_vector_c>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                        ),
                    ]
                ),
                SM(
                    sections=["cp2k_section_functional"],
                    startReStr=" FUNCTIONAL\|",
                    forwardMatch=True,
                    otherMetaInfo=["XC_functional"],
                    subMatchers=[
                        SM(
                            repeats=True,
                            startReStr=" FUNCTIONAL\| (?P<cp2k_functional_name>[\w\d\W]+):"
                        )
                    ]
                ),
                SM(
                    sections=["cp2k_section_total_numbers"],
                    startReStr=" TOTAL NUMBERS AND MAXIMUM NUMBERS",
                    subMatchers=[
                        SM(
                            startReStr="\s+- Atoms:\s+(?P<number_of_atoms>\d+)",
                            sections=["section_system_description"]
                        ),
                        SM(
                            startReStr="\s+- Shell sets:\s+(?P<cp2k_shell_sets>\d+)"
                        )
                    ]
                ),
                SM(
                    sections=["cp2k_section_md"],
                    startReStr=" MD| Molecular Dynamics Protocol",
                    forwardMatch=True,
                    subMatchers=[
                        SM(
                            repeats=True,
                            startReStr=" ENERGY\| Total FORCE_EVAL",
                            sections=["cp2k_section_md_step"],
                            subMatchers=[
                                SM(
                                    startReStr=" ATOMIC FORCES in \[a\.u\.\]",
                                    sections=["cp2k_section_md_forces"],
                                    subMatchers=[
                                        SM(
                                            startReStr="\s+\d+\s+\d+\s+[\w\W\d]+\s+(?P<cp2k_md_force_atom_string>{0}\s+{0}\s+{0})".format(self.f_regex),
                                            sections=["cp2k_section_md_force_atom"],
                                            repeats=True,
                                        )
                                    ]
                                ),
                                SM(
                                    startReStr=" STEP NUMBER\s+=\s+(?P<cp2k_md_step_number>\d+)"
                                ),
                                SM(
                                    startReStr=" TIME \[fs\]\s+=\s+(?P<cp2k_md_step_time>\d+\.\d+)"
                                ),
                                SM(
                                    startReStr=" TEMPERATURE \[K\]\s+=\s+(?P<cp2k_md_temperature_instantaneous>{0})\s+(?P<cp2k_md_temperature_average>{0})".format(self.f_regex)
                                ),
                                SM(
                                    startReStr=" i =",
                                    sections=["cp2k_section_md_coordinates"],
                                    otherMetaInfo=["cp2k_md_coordinates"],
                                    dependencies={"cp2k_md_coordinates": ["cp2k_md_coordinate_atom_string"]},
                                    subMatchers=[
                                        SM(
                                            startReStr=" \w+\s+(?P<cp2k_md_coordinate_atom_string>{0}\s+{0}\s+{0})".format(self.f_regex),
                                            endReStr="\n",
                                            sections=["cp2k_section_md_coordinate_atom"],
                                            repeats=True,
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        #=======================================================================
        # The cache settings
        self.cachingLevelForMetaName = {
            'cp2k_cell_vector_a': CachingLevel.Cache,
            'cp2k_cell_vector_b': CachingLevel.Cache,
            'cp2k_cell_vector_c': CachingLevel.Cache,
            'cp2k_section_cell': CachingLevel.Cache,
            'cp2k_functional_name': CachingLevel.Cache,
            'cp2k_section_functionals': CachingLevel.Cache,
            'cp2k_section_numbers': CachingLevel.Cache,
            'cp2k_atom_number': CachingLevel.Cache,
            'cp2k_shell_sets': CachingLevel.Cache,

            'cp2k_section_md_coordinates': CachingLevel.Cache,
            'cp2k_section_md_coordinate_atom': CachingLevel.Cache,
            'cp2k_md_coordinate_atom_string': CachingLevel.Cache,
            'cp2k_md_coordinate_atom_float': CachingLevel.Cache,

            'cp2k_section_md_forces': CachingLevel.Cache,
            'cp2k_section_md_force_atom': CachingLevel.Cache,
            'cp2k_md_force_atom_string': CachingLevel.Cache,
            'cp2k_md_force_atom_float': CachingLevel.Cache,
        }

    #===========================================================================
    # The functions that trigger when sections are closed
    def onClose_cp2k_section_cell(self, backend, gIndex, section):
        """When the cell definition finishes, gather the results to a 3x3
        matrix. Or if not present, ask the cp2kparser for help.
        """
        # Open the common system description section
        gIndex = backend.openSection("section_system_description")

        # Get the cell vector strings
        a = section["cp2k_cell_vector_a"][0]
        b = section["cp2k_cell_vector_b"][0]
        c = section["cp2k_cell_vector_c"][0]

        # Extract the components and put into numpy array
        a_comp = a.split()
        b_comp = b.split()
        c_comp = c.split()

        cell = np.zeros((3, 3))
        cell[0, :] = a_comp
        cell[1, :] = b_comp
        cell[2, :] = c_comp

        backend.addArrayValues("simulation_cell", cell, unit="angstrom")

        # Close the common system description section
        backend.closeSection("section_system_description", gIndex)

    def onClose_cp2k_section_functional(self, backend, gIndex, section):
        """When all the functional definitions have been gathered, matches them
        with the nomad correspondents and combines into one single string which
        is put into the backend.
        """
        # Get the list of functional names
        functional_names = section["cp2k_functional_name"]

        # Define a mapping for the functionals
        functional_map = {
            "LYP": "GGA_C_LYP",
            "BECKE88": "GGA_X_B88",
            "PADE": "LDA_XC_TETER93",
            "LDA": "LDA_XC_TETER93",
            "BLYP": "HYB_GGA_XC_B3LYP",
        }

        # Match eatch cp2k functional name and sort the matches into a list
        functionals = []
        for name in functional_names:
            match = functional_map.get(name)
            if match:
                functionals.append(match)
        functionals = "_".join(sorted(functionals))

        # Push the functional string into the backend
        gIndex = backend.openSection("section_method")
        backend.addValue('XC_functional', functionals)
        backend.closeSection("section_method", gIndex)

    # def onClose_cp2k_section_atom_position(self, backend, gIndex, section):
        # """Get the initial atomic positions from cp2kparser.
        # """
        # pass
        # positions, unit = self.cp2kparser.get_initial_atom_positions_and_unit()
        # backend.addArrayValues("atom_position", positions)

    def onClose_cp2k_section_md_coordinate_atom(self, backend, gIndex, section):
        """Given the string with the coordinate components for one atom, make it
        into a numpy array of coordinate components and store for later
        concatenation.
        """
        force_string = section["cp2k_md_coordinate_atom_string"][0]
        components = np.array([float(x) for x in force_string.split()])
        backend.addArrayValues("cp2k_md_coordinate_atom_float", components)

    def onClose_cp2k_section_md_coordinates(self, backend, gIndex, section):
        """When all the coordinates for individual atoms have been gathered,
        concatenate them into one big array and forward to the backend.
        """
        forces = section["cp2k_md_coordinate_atom_float"]
        forces = np.array(forces)
        backend.addArrayValues("cp2k_md_coordinates", forces)

    def onClose_cp2k_section_md_force_atom(self, backend, gIndex, section):
        """Given the string with the force components for one atom, make it
        into a numpy array of force components and store for later
        concatenation.
        """
        force_string = section["cp2k_md_force_atom_string"][0]
        components = np.array([float(x) for x in force_string.split()])
        backend.addArrayValues("cp2k_md_force_atom_float", components)

    def onClose_cp2k_section_md_forces(self, backend, gIndex, section):
        """When all the forces for individual atoms have been gathered,
        concatenate them into one big array and forward to the backend.
        """
        forces = section["cp2k_md_force_atom_float"]
        forces = np.array(forces)
        backend.addArrayValues("cp2k_md_forces", forces, unit="force_au")

    #===========================================================================
    # adHoc functions that are used to do custom parsing.
