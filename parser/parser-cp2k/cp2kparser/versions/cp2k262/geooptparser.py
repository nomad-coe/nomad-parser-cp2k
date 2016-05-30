from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.baseclasses import MainHierarchicalParser
from commonmatcher import CommonMatcher
from cp2kparser.generic.configurationreading import iread
from nomadcore.caching_backend import CachingLevel
import logging
import ase.io
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
        self.setup_common_matcher(CommonMatcher(parser_context))
        self.traj_iterator = None

        #=======================================================================
        # Cached values
        self.cache_service.add_cache_object("number_of_frames_in_sequence", 0, single=True, update=True)
        self.cache_service.add_cache_object("frame_sequence_potential_energy", [], single=True, update=True)

        #=======================================================================
        # Cache levels
        self.caching_level_for_metaname.update({
            'x_cp2k_optimization_energy': CachingLevel.ForwardAndCache,
            'x_cp2k_optimization_step_size_convergence_limit': CachingLevel.ForwardAndCache,
            'x_cp2k_section_geometry_optimization_information': CachingLevel.ForwardAndCache,
        })

        #=======================================================================
        # SimpleMatchers
        self.geo_opt = SM(
            " ***                     STARTING GEOMETRY OPTIMIZATION                      ***".replace("*", "\*"),
            sections=["section_frame_sequence"],
            subMatchers=[
                SM( " ***                           CONJUGATE GRADIENTS                           ***".replace("*", "\*"),
                    adHoc=self.adHoc_conjugate_gradient()
                ),
                SM( " --------  Informations at step",
                    forwardMatch=True,
                    name="geooptstep",
                    repeats=True,
                    sections=["section_single_configuration_calculation", "section_system"],
                    subMatchers=[
                        SM( " --------  Informations at step",
                            sections=["x_cp2k_section_geometry_optimization_information"],
                            subMatchers=[
                                SM( "  Optimization Method        =\s+(?P<x_cp2k_optimization_method>{})".format(self.cm.regex_word)),
                                SM( "  Total Energy               =\s+(?P<x_cp2k_optimization_energy__hartree>{})".format(self.cm.regex_f)),
                                SM( "  Real energy change         =\s+(?P<x_cp2k_optimization_energy_change__hartree>{})".format(self.cm.regex_f)),
                                SM( "  Decrease in energy         =\s+(?P<x_cp2k_optimization_energy_decrease>{})".format(self.cm.regex_word)),
                                SM( "  Used time                  =\s+(?P<x_cp2k_optimization_used_time>{})".format(self.cm.regex_f)),
                                SM( "  Max. step size             =\s+(?P<x_cp2k_optimization_max_step_size__bohr>{})".format(self.cm.regex_f)),
                                SM( "  Conv. limit for step size  =\s+(?P<x_cp2k_optimization_step_size_convergence_limit__bohr>{})".format(self.cm.regex_f)),
                                SM( "  Convergence in step size   =\s+(?P<x_cp2k_optimization_step_size_convergence>{})".format(self.cm.regex_word)),
                                SM( "  RMS step size              =\s+(?P<x_cp2k_optimization_rms_step_size__bohr>{})".format(self.cm.regex_f)),
                                SM( "  Convergence in RMS step    =\s+(?P<x_cp2k_optimization_rms_step_size_convergence>{})".format(self.cm.regex_word)),
                                SM( "  Max. gradient              =\s+(?P<x_cp2k_optimization_max_gradient__bohr_1hartree>{})".format(self.cm.regex_f)),
                                SM( "  Conv. limit for gradients  =\s+(?P<x_cp2k_optimization_gradient_convergence_limit__bohr_1hartree>{})".format(self.cm.regex_f)),
                                SM( "  Conv. for gradients        =\s+(?P<x_cp2k_optimization_max_gradient_convergence>{})".format(self.cm.regex_word)),
                                SM( "  RMS gradient               =\s+(?P<x_cp2k_optimization_rms_gradient__bohr_1hartree>{})".format(self.cm.regex_f)),
                                SM( "  Conv. in RMS gradients     =\s+(?P<x_cp2k_optimization_rms_gradient_convergence>{})".format(self.cm.regex_word)),
                            ],
                            adHoc=self.adHoc_step()
                        ),
                    ]
                ),
                SM( " ***                    GEOMETRY OPTIMIZATION COMPLETED                      ***".replace("*", "\*"),
                    adHoc=self.adHoc_geo_opt_converged())
            ],
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
                        self.cm.quickstep(),
                    ],
                ),
                self.geo_opt
            ]
        )

    #===========================================================================
    # onClose triggers
    def onClose_section_frame_sequence(self, backend, gIndex, section):
        self.cache_service.push_value("number_of_frames_in_sequence")
        self.cache_service.push_array_values("frame_sequence_potential_energy")

        opt_section = section["x_cp2k_section_geometry_optimization_information"]
        if opt_section is not None:
            opt_section = opt_section[-1]
            geo_limit = opt_section["x_cp2k_optimization_step_size_convergence_limit"]
            if geo_limit is not None:
                self.backend.addValue("geometry_optimization_geometry_change", geo_limit[0])
            force_limit = opt_section["x_cp2k_optimization_gradient_convergence_limit"]
            if force_limit is not None:
                self.backend.addValue("geometry_optimization_threshold_force", force_limit[0])

    def onClose_section_sampling_method(self, backend, gIndex, section):
        self.backend.addValue("sampling_method", "geometry_optimization")

    def onClose_x_cp2k_section_geometry_optimization_information(self, backend, gIndex, section):
        energy = section["x_cp2k_optimization_energy"][0]
        self.cache_service["frame_sequence_potential_energy"].append(energy)

    def onClose_section_method(self, backend, gIndex, section):
        traj_file = self.file_service.get_file_by_id("trajectory")
        if traj_file is not None:
            try:
                self.traj_iterator = iread(traj_file)
            except ValueError:
                # The format was not supported by ase
                pass

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
            parser.backend.addValue("geometry_optimization_method", "conjugate_gradient")
        return wrapper

    def adHoc_step(self):
        """Called when all the step information has been retrieved from the
        output file. Here further information is gathered from external files.
        """
        def wrapper(parser):
            self.cache_service["number_of_frames_in_sequence"] += 1

            # Get the next position from the trajectory file
            if self.traj_iterator is not None:
                pos = next(self.traj_iterator)
                self.cache_service["atom_positions"] = pos

        return wrapper

    def adHoc_setup_traj_file(self):
        def wrapper(parser):
            print "HERE"
        return wrapper

    def debug(self):
        def wrapper(parser):
            print "FOUND"
        return wrapper
