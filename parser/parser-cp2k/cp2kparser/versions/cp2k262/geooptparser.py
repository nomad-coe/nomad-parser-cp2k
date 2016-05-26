from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.baseclasses import MainHierarchicalParser
from commonmatcher import CommonMatcher
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
        })

        #=======================================================================
        # SimpleMatchers
        self.geo_opt = SM(
            " ***                     STARTING GEOMETRY OPTIMIZATION                      ***".replace("*", "\*"),
            sections=["section_frame_sequence", "section_sampling_method"],
            subMatchers=[
                SM( " --------  Informations at step =\s+{}\s+------------".format(self.cm.regex_i),
                    forwardMatch=True,
                    name="geooptstep",
                    repeats=True,
                    sections=["section_single_configuration_calculation", "section_system"],
                    subMatchers=[
                        SM( " --------  Informations at step =\s+{}\s+------------".format(self.cm.regex_i),
                            sections=["x_cp2k_section_geometry_optimization_information"],
                            subMatchers=[
                                SM( "  Optimization Method        =\s+(?P<x_cp2k_optimization_method>{})".format(self.cm.regex_word)),
                                SM( "  Total Energy               =\s+(?P<x_cp2k_optimization_energy__hartree>{})".format(self.cm.regex_f)),
                                SM( "  Real energy change         =\s+(?P<x_cp2k_optimization_energy_change__hartree>{})".format(self.cm.regex_f)),
                                SM( "  Decrease in energy         =\s+(?P<x_cp2k_optimization_energy_decrease>{})".format(self.cm.regex_word)),
                                SM( "  Used time                  =\s+(?P<x_cp2k_optimization_used_time>{})".format(self.cm.regex_f)),
                                SM( "  Max. step size             =\s+(?P<x_cp2k_optimization_max_step_size__bohr>{})".format(self.cm.regex_f)),
                                SM( "  Convergence in step size   =\s+(?P<x_cp2k_optimization_step_size_convergence>{})".format(self.cm.regex_word)),
                                SM( "  RMS step size              =\s+(?P<x_cp2k_optimization_rms_step_size__bohr>{})".format(self.cm.regex_f)),
                                SM( "  Convergence in RMS step    =\s+(?P<x_cp2k_optimization_rms_step_size_convergence>{})".format(self.cm.regex_word)),
                                SM( "  Max. gradient              =\s+(?P<x_cp2k_optimization_max_gradient__bohr_1hartree>{})".format(self.cm.regex_f)),
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
            sections=["section_run"],
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

    def onClose_x_cp2k_section_geometry_optimization_information(self, backend, gIndex, section):
        energy = section["x_cp2k_optimization_energy"][0]
        self.cache_service["frame_sequence_potential_energy"].append(energy)

    def onClose_section_method(self, backend, gIndex, section):
        traj_file = self.file_service.get_file_by_id("trajectory")
        try:
            if traj_file is not None:
                self.traj_iterator = ase.io.iread(traj_file)
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

    def adHoc_step(self):
        """Called when all the step information has been retrieved from the
        output file. Here further information is gathered from external files.
        """
        def wrapper(parser):
            self.cache_service["number_of_frames_in_sequence"] += 1

            # Get the next position from the trajectory file
            if self.traj_iterator is not None:
                atoms = next(self.traj_iterator)
                pos = atoms.positions
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
