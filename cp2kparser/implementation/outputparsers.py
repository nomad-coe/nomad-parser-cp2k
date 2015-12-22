from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.caching_backend import CachingLevel
import numpy as np


#===============================================================================
class CP2KOutputParser262(object):
    """The object that goes through the CP2K output file and parses everything
    it can using the SimpleParser architecture.
    """

    def __init__(self, cp2kparser, metaInfoToKeep=None, metaInfoToSkip=None):
        """Initialize an output parser. The outputparser will sometimes ask the
        CP2KParser for information. E.g. the auxiliary coordinate files are
        identified and read by the CP2KParser.
        """
        self.cp2kparser = cp2kparser
        self.metaInfoToKeep = metaInfoToKeep
        self.metaInfoToSkip = metaInfoToSkip

        # Define the output parsing tree for this version
        self.outputstructure = SM(
            name='root',
            startReStr="",
            subMatchers=[
                SM(
                    name='new_run',
                    startReStr=r" DBCSR\| Multiplication driver",
                    endReStr="[.\*]+PROGRAM STOPPED IN",
                    required=True,
                    sections=['section_run'],
                    subMatchers=[
                        SM(
                            name="run_datetime",
                            startReStr=r"[\*\s]+PROGRAM STARTED AT\s+(?P<cp2k_run_start_date>\d{4}-\d{2}-\d{2}) (?P<cp2k_run_start_time>\d{2}:\d{2}:\d{2}.\d{3})",
                        ),
                        SM(
                            name="version",
                            startReStr=r" CP2K\| version string:\s+(?P<program_version>[\w\d\W\s]+)",
                        ),
                        SM(
                            name="svn_revision",
                            startReStr=r" CP2K\| source code revision number:\s+svn:(?P<cp2k_svn_revision>\d+)",
                        ),
                        SM(
                            name="system",
                            startReStr="",
                            forwardMatch=True,
                            sections=["section_system_description"],
                            subMatchers=[
                                SM(
                                    name="cell",
                                    startReStr=" CELL\|",
                                    forwardMatch=True,
                                    sections=["cp2k_section_cell"],
                                    subMatchers=[
                                        SM(
                                            name="cell_a",
                                            startReStr=" CELL\| Vector a \[angstrom\]:\s+(?P<cp2k_cell_vector_a>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                                        ),
                                        SM(
                                            name="cell_b",
                                            startReStr=" CELL\| Vector b \[angstrom\]:\s+(?P<cp2k_cell_vector_b>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                                        ),
                                        SM(
                                            name="cell_c",
                                            startReStr=" CELL\| Vector c \[angstrom\]:\s+(?P<cp2k_cell_vector_c>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                                        ),
                                    ]
                                ),
                                SM(
                                    name="positions",
                                    sections=["cp2k_section_atom_position"],
                                    startReStr="",
                                )
                            ]
                        ),
                        SM(
                            name="functionals",
                            startReStr=" FUNCTIONAL\|",
                            forwardMatch=True,
                            sections=["section_method", "cp2k_section_functionals"],
                            subMatchers=[
                                SM(
                                    name="functional",
                                    repeats=True,
                                    startReStr=" FUNCTIONAL\| (?P<cp2k_functional_name>[\w\d\W]+):"
                                )
                            ]
                        ),
                        SM(
                            name="numbers",
                            startReStr=" TOTAL NUMBERS AND MAXIMUM NUMBERS",
                            sections=["cp2k_section_numbers"],
                            subMatchers=[
                                SM(
                                    name="number_of_atoms",
                                    startReStr="\s+- Atoms:\s+(?P<cp2k_atom_number>\d+)"
                                ),
                                SM(
                                    name="number_of_shell_sets",
                                    startReStr="\s+- Shell sets:\s+(?P<cp2k_shell_sets>\d+)"
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        # The cache settings
        self.cachingLevelForMetaName = {
            'cp2k_cell_vector_a': CachingLevel.Cache,
            'cp2k_cell_vector_b': CachingLevel.Cache,
            'cp2k_cell_vector_c': CachingLevel.Cache,
            'cp2k_section_cell': CachingLevel.Cache,
            'cp2k_section_atom_position': CachingLevel.Cache,
            'cp2k_functional_name': CachingLevel.Cache,
            'cp2k_section_functionals': CachingLevel.Cache,
            'cp2k_section_numbers': CachingLevel.Cache,
            'cp2k_atom_number': CachingLevel.Cache,
            'cp2k_shell_sets': CachingLevel.Cache,
        }

    # The trigger functions
    def onClose_cp2k_section_cell(self, backend, gIndex, section):
        """When the cell definition finishes, gather the results to a 3x3
        matrix. Or if not present, ask the cp2kparser for help.
        """
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

        backend.addArrayValues("cell", cell)

    def onClose_cp2k_section_functionals(self, backend, gIndex, section):
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
        backend.addValue('XC_functional', functionals)

    def onClose_cp2k_section_atom_position(self, backend, gIndex, section):
        """Get the initial atomic positions from cp2kparser.
        """
        positions, unit = self.cp2kparser.get_initial_atom_positions_and_unit()
        backend.addArrayValues("atom_position", positions)

    # def onClose_section_run(self, backend, gIndex, section):
        # """At the end the parser is able to place the final cached values into
        # the backend.
        # """
