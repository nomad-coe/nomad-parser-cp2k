import re
from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.caching_backend import CachingLevel
from cp2kparser.utils.baseclasses import FileParser
import numpy as np


#===============================================================================
class CP2KOutputParser262(FileParser):
    """The object that goes through the CP2K output file and parses everything
    it can using the SimpleParser architecture.
    """

    def __init__(self, files, parser_context):
        """Initialize an output parser.
        """
        FileParser.__init__(self, files, parser_context)
        self.f_regex = "-?\d+\.\d+(?:E+|-\d+)?"  # Regex for a floating point value

        # Define the output parsing tree for this version
        self.root_matcher = SM(
            startReStr="",
            sections=['section_run'],
            subMatchers=[
                SM(
                    sections=['cp2k_section_dbcsr'],
                    startReStr=r" DBCSR\| Multiplication driver",
                ),
                SM(
                    sections=['cp2k_section_startinformation'],
                    startReStr=r" \*\*\*\* \*\*\*\* \*\*\*\*\*\*  \*\*  PROGRAM STARTED AT",
                    forwardMatch=True,
                    subMatchers=[
                        SM(
                            startReStr=r" \*\*\*\* \*\*\*\* \*\*\*\*\*\*  \*\*  PROGRAM STARTED AT\s+(?P<cp2k_run_start_date>\d{4}-\d{2}-\d{2}) (?P<cp2k_run_start_time>\d{2}:\d{2}:\d{2}.\d{3})",
                        ),
                    ]
                ),
                SM(
                    sections=['cp2k_section_programinformation'],
                    startReStr=r" CP2K\|",
                    forwardMatch=True,
                    subMatchers=[
                        SM(
                            startReStr=r" CP2K\| version string:\s+(?P<program_version>[\w\d\W\s]+)",
                        ),
                        SM(
                            startReStr=r" CP2K\| source code revision number:\s+svn:(?P<cp2k_svn_revision>\d+)",
                        ),
                    ]
                ),
                SM(
                    # sections=["cp2k_section_cell"],
                    startReStr=" CELL\|",
                    adHoc=self.adHoc_cp2k_section_cell()
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
                    # sections=["cp2k_section_quickstep_atom_information"],
                    startReStr=" MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom",
                    adHoc=self.adHoc_cp2k_section_quickstep_atom_information(),
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
        self.caching_level_for_metaname = {
            'cp2k_functional_name': CachingLevel.Cache,
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
    def adHoc_cp2k_section_cell(self):
        """Used to extract the cell information.
        """
        def wrapper(parser):
            # Read the lines containing the cell vectors
            a_line = parser.fIn.readline()
            b_line = parser.fIn.readline()
            c_line = parser.fIn.readline()

            # Define the regex that extracts the components and apply it to the lines
            regex_string = r" CELL\| Vector \w \[angstrom\]:\s+({0})\s+({0})\s+({0})".format(self.f_regex)
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
            gIndex = parser.backend.openSection("section_system_description")
            parser.backend.addArrayValues("simulation_cell", cell, unit="angstrom")
            parser.backend.closeSection("section_system_description", gIndex)

        return wrapper

    def adHoc_cp2k_section_quickstep_atom_information(self):
        """Used to extract the initial atomic coordinates and names in the
        Quickstep module.
        """
        def wrapper(parser):

            # Define the regex that extracts the information
            regex_string = r"\s+\d+\s+\d+\s+(\w+)\s+\d+\s+({0})\s+({0})\s+({0})".format(self.f_regex)
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
                gIndex = parser.backend.openSection("section_system_description")
                parser.backend.addArrayValues("atom_position", coordinates, unit="angstrom")
                parser.backend.addArrayValues("atom_label", labels)
                parser.backend.closeSection("section_system_description", gIndex)

        return wrapper
