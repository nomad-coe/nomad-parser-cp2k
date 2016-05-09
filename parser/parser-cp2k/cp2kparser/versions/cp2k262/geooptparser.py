from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.baseclasses import MainHierarchicalParser
from commonmatcher import CommonMatcher
import logging
logger = logging.getLogger("nomad")


#===============================================================================
class CP2KGeoOptParser(MainHierarchicalParser):
    """Used to parse the CP2K calculation with run types:
        -GEO_OPT/GEOMETRY_OPTIMIZATION
    """
    def __init__(self, file_path, parser_context):
        """
        """
        super(CP2KGeoOptParser, self).__init__(file_path, parser_context)
        self.cm = CommonMatcher(parser_context)

        # Simple matcher for run type ENERGY_FORCE, ENERGY with QUICKSTEP
        self.geo_opt = SM(
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
                self.geo_opt
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

    #===========================================================================
    # adHoc functions. Primarily these
    # functions are used for data that is formatted as a table or a list.
