from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.baseclasses import MainHierarchicalParser
from singlepointforceparser import CP2KSinglePointForceParser
from nomadcore.caching_backend import CachingLevel
from commonmatcher import CommonMatcher
from cp2kparser.generic.utils import try_to_add_value, try_to_add_array_values
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
        # Cache levels
        self.caching_level_for_metaname.update({
            'x_cp2k_energy_total_scf_iteration': CachingLevel.ForwardAndCache,
            'x_cp2k_energy_XC_scf_iteration': CachingLevel.ForwardAndCache,
            'x_cp2k_energy_change_scf_iteration': CachingLevel.ForwardAndCache,
            'x_cp2k_stress_tensor': CachingLevel.ForwardAndCache,
            'x_cp2k_section_stress_tensor': CachingLevel.ForwardAndCache,
        })

        #=======================================================================
        # SimpleMatchers
        self.root_matcher = SM("",
            forwardMatch=True,
            sections=['section_run', "section_single_configuration_calculation", "section_system", "section_method"],
            otherMetaInfo=["atom_forces"],
            subMatchers=[
                self.cm.header(),
                self.cm.quickstep_header(),
                self.cm.quickstep_calculation(),
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

    def onClose_x_cp2k_section_scf_iteration(self, backend, gIndex, section):
        """Keep track of how many SCF iteration are made."""
        self.cache_service["number_of_scf_iterations"] += 1
        gId = backend.openSection("section_scf_iteration")
        try_to_add_value(backend, section, "x_cp2k_energy_total_scf_iteration", "energy_total_scf_iteration")
        try_to_add_value(backend, section, "x_cp2k_energy_XC_scf_iteration", "energy_XC_scf_iteration")
        try_to_add_value(backend, section, "x_cp2k_energy_change_scf_iteration", "energy_change_scf_iteration")
        backend.closeSection("section_scf_iteration", gId)

    def onClose_x_cp2k_section_quickstep_calculation(self, backend, gIndex, section):
        """"""
        try_to_add_value(backend, section, "x_cp2k_energy_total", "energy_total")
        try_to_add_value(backend, section, "x_cp2k_electronic_kinetic_energy", "electronic_kinetic_energy")
        try_to_add_value(backend, section, "x_cp2k_quickstep_converged", "single_configuration_calculation_converged")
        try_to_add_array_values(backend, section, "x_cp2k_atom_forces", "atom_forces")

    def onClose_x_cp2k_section_stress_tensor(self, backend, gIndex, section):
        """"""
        gId = backend.openSection("section_stress_tensor")
        try_to_add_array_values(backend, section, "x_cp2k_stress_tensor", "stress_tensor")
        backend.closeSection("section_stress_tensor", gId)

    #===========================================================================
    # adHoc functions
