from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.caching_backend import CachingLevel


#===============================================================================
class CP2KOutputParser262(object):
    """The object that goes through the CP2K outputfile and parses everything
    it can using the SimpleParser architecture.
    """

    # Define the output parsing tree for this version
    outputstructure = SM(
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
                        name="cell",
                        startReStr=" CELL\|",
                        forwardMatch=True,
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
                    )
                ]
            )
        ]
    )

    # The cache settings
    cachingLevelForMetaName = {
        'cp2k_cell_vector_a': CachingLevel.Cache,
        'cp2k_cell_vector_b': CachingLevel.Cache,
        'cp2k_cell_vector_c': CachingLevel.Cache,
    }

    # The trigger functions
    def onClose_section_single_configuration_calculation(self, backend, gIndex, section):
        """trigger called when section_single_configuration_calculation is closed"""
        backend.addValue('scf_dft_number_of_iterations', self.scfIterNr)
        # start with -1 since zeroth iteration is the initialization
        self.scfIterNr = -1
