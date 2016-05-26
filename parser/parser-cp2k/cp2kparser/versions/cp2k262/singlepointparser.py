from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.baseclasses import MainHierarchicalParser
from singlepointforceparser import CP2KSinglePointForceParser
from commonmatcher import CommonMatcher
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
        self.setup_common_matcher(CommonMatcher(parser_context))

        #=======================================================================
        # SimpleMatchers
        self.root_matcher = SM("",
            forwardMatch=True,
            sections=['section_run', "section_single_configuration_calculation", "section_system", "section_method"],
            otherMetaInfo=["atom_forces"],
            subMatchers=[
                self.cm.header(),
                self.cm.quickstep(),
                self.cm.scf()
            ]
        )

    #===========================================================================
    # onClose triggers
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

        # Only in the single configuration calculations the number of scf
        # iterations is given. E.g. in geometry optimization there are multiple
        # scf calculations so this loses it's meaning sort of.
        self.cache_service.push_value("number_of_scf_iterations")
        self.cache_service["number_of_scf_iterations"] = 0

    #===========================================================================
    # adHoc functions
