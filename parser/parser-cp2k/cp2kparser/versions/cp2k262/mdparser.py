from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.baseclasses import MainHierarchicalParser
from commonmatcher import CommonMatcher
import cp2kparser.generic.configurationreading
import cp2kparser.generic.csvparsing
from nomadcore.caching_backend import CachingLevel
import logging
logger = logging.getLogger("nomad")


#===============================================================================
class CP2KMDParser(MainHierarchicalParser):
    """Used to parse the CP2K calculation with run types:
        -MD
        -MOLECULAR_DYNAMICS
    """
    def __init__(self, file_path, parser_context):
        """
        """
        super(CP2KMDParser, self).__init__(file_path, parser_context)
        self.setup_common_matcher(CommonMatcher(parser_context))
        self.traj_iterator = None

        #=======================================================================
        # Globally cached values
        self.cache_service.add_cache_object("number_of_frames_in_sequence", 0)
        self.cache_service.add_cache_object("frame_sequence_potential_energy", [])
        self.cache_service.add_cache_object("frame_sequence_local_frames_ref", [])

        #=======================================================================
        # Cache levels
        self.caching_level_for_metaname.update({
            # 'x_cp2k_optimization_energy': CachingLevel.ForwardAndCache,
            # 'x_cp2k_section_geometry_optimization_step': CachingLevel.ForwardAndCache,
            # 'x_cp2k_section_quickstep_calculation': CachingLevel.ForwardAndCache,
            # 'x_cp2k_section_geometry_optimization': CachingLevel.ForwardAndCache,
            # 'x_cp2k_section_geometry_optimization_energy_reevaluation': CachingLevel.ForwardAndCache,
        })

        #=======================================================================
        # SimpleMatchers
        self.md = SM(
            " MD\| Molecular Dynamics Protocol",
            sections=["x_cp2k_section_md"],
            subMatchers=[
                SM( " MD\| Ensemble Type\s+(?P<x_cp2k_md_ensemble_type>{})".format(self.cm.regex_word)),
                SM( " MD\| Number of Time Steps\s+(?P<x_cp2k_md_number_of_time_steps>{})".format(self.cm.regex_word)),
                SM( " MD\| Time Step \[fs\]\s+(?P<x_cp2k_md_time_step__fs>{})".format(self.cm.regex_f)),
                SM( " MD\| Temperature \[K\]\s+(?P<x_cp2k_md_temperature>{})".format(self.cm.regex_f)),
                SM( " MD\| Temperature tolerance \[K\]\s+(?P<x_cp2k_md_temperature_tolerance>{})".format(self.cm.regex_f)),
                SM( " MD\| Print MD information every\s+(?P<x_cp2k_md_print_frequency>{}) step(s)".format(self.cm.regex_i)),
                SM( " MD\| File type     Print frequency\[steps\]                             File names"),
                SM( " MD\| Coordinates\s+(?P<x_cp2k_md_coordinates_print_frequency>{})\s+(?P<x_cp2k_md_coordinates_filename>{})".format(self.cm.regex_i, self.cm.regex_word)),
                SM( " MD\| Velocities\s+(?P<x_cp2k_md_velocities_print_frequency>{})\s+(?P<x_cp2k_md_velocities_filename>{})".format(self.cm.regex_i, self.cm.regex_word)),
                SM( " MD\| Energies\s+(?P<x_cp2k_md_energies_print_frequency>{})\s+(?P<x_cp2k_md_energies_filename>{})".format(self.cm.regex_i, self.cm.regex_word)),
                SM( " MD\| Dump\s+(?P<x_cp2k_md_dump_print_frequency>{})\s+(?P<x_cp2k_md_dump_filename>{})".format(self.cm.regex_i, self.cm.regex_word)),
            ]
        )

        # Compose root matcher according to the run type. This way the
        # unnecessary regex parsers will not be compiled and searched. Saves
        # computational time.
        self.root_matcher = SM("",
            forwardMatch=True,
            sections=["section_run", "section_sampling_method"],
            subMatchers=[
                SM( "",
                    forwardMatch=True,
                    sections=["section_method"],
                    subMatchers=[
                        self.cm.header(),
                        self.cm.quickstep_header(),
                    ],
                ),
                self.md,
            ]
        )

    #===========================================================================
    # onClose triggers
    def onClose_x_cp2k_section_geometry_optimization(self, backend, gIndex, section):

        # Get the re-evaluated energy and add it to frame_sequence_potential_energy
        energy = section.get_latest_value([
            "x_cp2k_section_geometry_optimization_energy_reevaluation",
            "x_cp2k_section_quickstep_calculation",
            "x_cp2k_energy_total"]
        )
        if energy is not None:
            self.cache_service["frame_sequence_potential_energy"].append(energy)

        # Push values from cache
        self.cache_service.push_array_values("frame_sequence_potential_energy")
        self.cache_service.push_value("geometry_optimization_method")
        self.backend.addValue("frame_sequence_to_sampling_ref", 0)

        # Get the optimization convergence criteria from the last optimization
        # step
        section.add_latest_value([
            "x_cp2k_section_geometry_optimization_step",
            "x_cp2k_optimization_step_size_convergence_limit"],
            "geometry_optimization_geometry_change",
        )
        section.add_latest_value([
            "x_cp2k_section_geometry_optimization_step",
            "x_cp2k_optimization_gradient_convergence_limit"],
            "geometry_optimization_threshold_force",
        )

        # Push the information into single configuration and system
        steps = section["x_cp2k_section_geometry_optimization_step"]
        each = self.cache_service["each_geo_opt"]
        add_last = False
        add_last_setting = self.cache_service["traj_add_last"]
        if add_last_setting == "NUMERIC" or add_last_setting == "SYMBOLIC":
            add_last = True

        # Push the trajectory
        n_steps = len(steps) + 1
        last_step = n_steps - 1
        for i_step in range(n_steps):
            singleId = backend.openSection("section_single_configuration_calculation")
            systemId = backend.openSection("section_system")

            if self.traj_iterator is not None:
                if (i_step + 1) % each == 0 or (i_step == last_step and add_last):
                    try:
                        pos = next(self.traj_iterator)
                    except StopIteration:
                        logger.error("Could not get the next geometries from an external file. It seems that the number of optimization steps in the CP2K outpufile doesn't match the number of steps found in the external trajectory file.")
                    else:
                        backend.addArrayValues("atom_positions", pos, unit="angstrom")
            backend.closeSection("section_system", systemId)
            backend.closeSection("section_single_configuration_calculation", singleId)

        self.cache_service.push_array_values("frame_sequence_local_frames_ref")
        backend.addValue("number_of_frames_in_sequence", n_steps)

    def onClose_section_sampling_method(self, backend, gIndex, section):
        self.backend.addValue("sampling_method", "geometry_optimization")

    def onClose_x_cp2k_section_geometry_optimization_step(self, backend, gIndex, section):
        energy = section["x_cp2k_optimization_energy"]
        if energy is not None:
            self.cache_service["frame_sequence_potential_energy"].append(energy[0])

    def onClose_section_method(self, backend, gIndex, section):
        traj_file = self.file_service.get_file_by_id("trajectory")
        traj_format = self.cache_service["trajectory_format"]
        if traj_format is not None and traj_file is not None:

            # Use special parsing for CP2K pdb files because they don't follow the proper syntax
            if traj_format == "PDB":
                self.traj_iterator = cp2kparser.generic.csvparsing.iread(traj_file, columns=[3, 4, 5], start="CRYST", end="END")
            else:
                try:
                    self.traj_iterator = cp2kparser.generic.configurationreading.iread(traj_file)
                except ValueError:
                    pass

    def onClose_section_single_configuration_calculation(self, backend, gIndex, section):
        self.cache_service["frame_sequence_local_frames_ref"].append(gIndex)

    #===========================================================================
    # adHoc functions
    def adHoc_geo_opt_converged(self):
        """Called when the geometry optimization converged.
        """
        def wrapper(parser):
            parser.backend.addValue("geometry_optimization_converged", True)
        return wrapper

    def adHoc_geo_opt_not_converged(self):
        """Called when the geometry optimization did not converge.
        """
        def wrapper(parser):
            parser.backend.addValue("geometry_optimization_converged", False)
        return wrapper

    def adHoc_conjugate_gradient(self):
        """Called when conjugate gradient method is used.
        """
        def wrapper(parser):
            self.cache_service["geometry_optimization_method"] = "conjugate_gradient"
        return wrapper

    def adHoc_bfgs(self):
        """Called when conjugate gradient method is used.
        """
        def wrapper(parser):
            self.cache_service["geometry_optimization_method"] = "bfgs"
        return wrapper

    # def adHoc_step(self):
        # """Called when all the step information has been retrieved from the
        # output file. Here further information is gathered from external files.
        # """
        # def wrapper(parser):
            # self.cache_service["number_of_frames_in_sequence"] += 1

        # return wrapper
