from __future__ import absolute_import
from builtins import next
from builtins import range
import numpy as np
from nomadcore.simple_parser import SimpleMatcher as SM
from nomadcore.baseclasses import MainHierarchicalParser
from .commonparser import CP2KCommonParser
import cp2kparser.generic.configurationreading
import cp2kparser.generic.csvparsing
from nomadcore.caching_backend import CachingLevel
from nomadcore.unit_conversion.unit_conversion import convert_unit
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
        self.setup_common_matcher(CP2KCommonParser(parser_context))
        self.traj_iterator = None
        self.vel_iterator = None
        self.energy_iterator = None
        self.cell_iterator = None
        self.n_steps = None
        self.output_freq = None
        self.coord_freq = None
        self.velo_freq = None
        self.energy_freq = None
        self.cell_freq = None
        self.md_quicksteps = []
        self.ensemble = None

        #=======================================================================
        # Globally cached values

        #=======================================================================
        # Cache levels
        self.caching_levels.update({
            'x_cp2k_section_md_settings': CachingLevel.ForwardAndCache,
            'x_cp2k_section_md_step': CachingLevel.ForwardAndCache,
            'x_cp2k_section_quickstep_calculation': CachingLevel.ForwardAndCache,
            "x_cp2k_section_scf_iteration": CachingLevel.ForwardAndCache,
            "x_cp2k_section_stress_tensor": CachingLevel.ForwardAndCache,
        })

        #=======================================================================
        # SimpleMatchers
        self.md = SM(
            " MD\| Molecular Dynamics Protocol",
            forwardMatch=True,
            sections=["section_frame_sequence", "x_cp2k_section_md"],
            subMatchers=[
                SM( " MD\| Molecular Dynamics Protocol",
                    forwardMatch=True,
                    sections=["section_sampling_method", "x_cp2k_section_md_settings"],
                    subMatchers=[
                        SM( " MD\| Ensemble Type\s+(?P<x_cp2k_md_ensemble_type>{})".format(self.regexs.regex_word)),
                        SM( " MD\| Number of Time Steps\s+(?P<x_cp2k_md_number_of_time_steps>{})".format(self.regexs.regex_i)),
                        SM( " MD\| Time Step \[fs\]\s+(?P<x_cp2k_md_time_step__fs>{})".format(self.regexs.regex_f)),
                        SM( " MD\| Temperature \[K\]\s+(?P<x_cp2k_md_target_temperature>{})".format(self.regexs.regex_f)),
                        SM( " MD\| Temperature tolerance \[K\]\s+(?P<x_cp2k_md_target_temperature_tolerance>{})".format(self.regexs.regex_f)),
                        SM( " MD\| Pressure \[Bar\]\s+(?P<x_cp2k_md_target_pressure>{})".format(self.regexs.regex_f)),
                        SM( " MD\| Barostat time constant \[  fs\]\s+(?P<x_cp2k_md_barostat_time_constant>{})".format(self.regexs.regex_f)),
                        SM( " MD\| Print MD information every\s+(?P<x_cp2k_md_print_frequency>{}) step\(s\)".format(self.regexs.regex_i)),
                        SM( " MD\| File type     Print frequency\[steps\]                             File names"),
                        SM( " MD\| Coordinates\s+(?P<x_cp2k_md_coordinates_print_frequency>{})\s+(?P<x_cp2k_md_coordinates_filename>{})".format(self.regexs.regex_i, self.regexs.regex_word)),
                        SM( " MD\| Simulation Cel\s+(?P<x_cp2k_md_simulation_cell_print_frequency>{})\s+(?P<x_cp2k_md_simulation_cell_filename>{})".format(self.regexs.regex_i, self.regexs.regex_word)),
                        SM( " MD\| Velocities\s+(?P<x_cp2k_md_velocities_print_frequency>{})\s+(?P<x_cp2k_md_velocities_filename>{})".format(self.regexs.regex_i, self.regexs.regex_word)),
                        SM( " MD\| Energies\s+(?P<x_cp2k_md_energies_print_frequency>{})\s+(?P<x_cp2k_md_energies_filename>{})".format(self.regexs.regex_i, self.regexs.regex_word)),
                        SM( " MD\| Dump\s+(?P<x_cp2k_md_dump_print_frequency>{})\s+(?P<x_cp2k_md_dump_filename>{})".format(self.regexs.regex_i, self.regexs.regex_word)),
                    ]
                ),
                SM( " ************************** Velocities initialization **************************".replace("*", "\*"),
                    name="md_initialization_step",
                    endReStr=" INITIAL CELL ANGLS",
                    sections=["x_cp2k_section_md_step"],
                    subMatchers=[
                        self.cm.quickstep_calculation(),
                        SM( " ******************************** GO CP2K GO! **********************************".replace("*", "\*")),
                        SM( " INITIAL POTENTIAL ENERGY\[hartree\]     =\s+(?P<x_cp2k_md_potential_energy_instantaneous__hartree>{})".format(self.regexs.regex_f)),
                        SM( " INITIAL KINETIC ENERGY\[hartree\]       =\s+(?P<x_cp2k_md_kinetic_energy_instantaneous__hartree>{})".format(self.regexs.regex_f)),
                        SM( " INITIAL TEMPERATURE\[K\]                =\s+(?P<x_cp2k_md_temperature_instantaneous>{})".format(self.regexs.regex_f)),
                        SM( " INITIAL BAROSTAT TEMP\[K\]              =\s+(?P<x_cp2k_md_barostat_temperature_instantaneous>{})".format(self.regexs.regex_f)),
                        SM( " INITIAL PRESSURE\[bar\]                 =\s+(?P<x_cp2k_md_pressure_instantaneous__bar>{})".format(self.regexs.regex_f)),
                        SM( " INITIAL VOLUME\[bohr\^3\]                =\s+(?P<x_cp2k_md_volume_instantaneous__bohr3>{})".format(self.regexs.regex_f)),
                        SM( " INITIAL CELL LNTHS\[bohr\]              =\s+(?P<x_cp2k_md_cell_length_a_instantaneous__bohr>{0})\s+(?P<x_cp2k_md_cell_length_b_instantaneous__bohr>{0})\s+(?P<x_cp2k_md_cell_length_c_instantaneous__bohr>{0})".format(self.regexs.regex_f)),
                        SM( " INITIAL CELL ANGLS\[deg\]               =\s+(?P<x_cp2k_md_cell_angle_a_instantaneous__deg>{0})\s+(?P<x_cp2k_md_cell_angle_b_instantaneous__deg>{0})\s+(?P<x_cp2k_md_cell_angle_c_instantaneous__deg>{0})".format(self.regexs.regex_f)),
                    ],
                    adHoc=self.adHoc_save_md_quickstep()
                ),
                SM( " SCF WAVEFUNCTION OPTIMIZATION",
                    endReStr=" TEMPERATURE \[K\]              =",
                    name="md_step",
                    forwardMatch=True,
                    repeats=True,
                    sections=["x_cp2k_section_md_step"],
                    subMatchers=[
                        self.cm.quickstep_calculation(),
                        SM( " ENSEMBLE TYPE                ="),
                        SM( " STEP NUMBER                  ="),
                        SM( " TIME \[fs\]                    =\s+(?P<x_cp2k_md_time__fs>{})".format(self.regexs.regex_f)),
                        SM( " CONSERVED QUANTITY \[hartree\] =\s+(?P<x_cp2k_md_conserved_quantity__hartree>{})".format(self.regexs.regex_f)),
                        SM( " CPU TIME \[s\]                 =\s+(?P<x_cp2k_md_cpu_time_instantaneous>{})\s+(?P<x_cp2k_md_cpu_time_average>{})".format(self.regexs.regex_f, self.regexs.regex_f)),
                        SM( " ENERGY DRIFT PER ATOM \[K\]    =\s+(?P<x_cp2k_md_energy_drift_instantaneous>{})\s+(?P<x_cp2k_md_energy_drift_average>{})".format(self.regexs.regex_f, self.regexs.regex_f)),
                        SM( " POTENTIAL ENERGY\[hartree\]    =\s+(?P<x_cp2k_md_potential_energy_instantaneous__hartree>{})\s+(?P<x_cp2k_md_potential_energy_average__hartree>{})".format(self.regexs.regex_f, self.regexs.regex_f)),
                        SM( " KINETIC ENERGY \[hartree\]     =\s+(?P<x_cp2k_md_kinetic_energy_instantaneous__hartree>{})\s+(?P<x_cp2k_md_kinetic_energy_average__hartree>{})".format(self.regexs.regex_f, self.regexs.regex_f)),
                        SM( " TEMPERATURE \[K\]              =\s+(?P<x_cp2k_md_temperature_instantaneous>{})\s+(?P<x_cp2k_md_temperature_average>{})".format(self.regexs.regex_f, self.regexs.regex_f)),
                        SM( " PRESSURE \[bar\]               =\s+(?P<x_cp2k_md_pressure_instantaneous__bar>{0})\s+(?P<x_cp2k_md_pressure_average__bar>{0})".format(self.regexs.regex_f)),
                        SM( " BAROSTAT TEMP\[K\]             =\s+(?P<x_cp2k_md_barostat_temperature_instantaneous>{0})\s+(?P<x_cp2k_md_barostat_temperature_average>{0})".format(self.regexs.regex_f)),
                        SM( " VOLUME\[bohr\^3\]               =\s+(?P<x_cp2k_md_volume_instantaneous__bohr3>{0})\s+(?P<x_cp2k_md_volume_average__bohr3>{0})".format(self.regexs.regex_f)),
                        SM( " CELL LNTHS\[bohr\]             =\s+(?P<x_cp2k_md_cell_length_a_instantaneous__bohr>{0})\s+(?P<x_cp2k_md_cell_length_b_instantaneous__bohr>{0})\s+(?P<x_cp2k_md_cell_length_c_instantaneous__bohr>{0})".format(self.regexs.regex_f)),
                        SM( " AVE. CELL LNTHS\[bohr\]        =\s+(?P<x_cp2k_md_cell_length_a_average__bohr>{0})\s+(?P<x_cp2k_md_cell_length_b_average__bohr>{0})\s+(?P<x_cp2k_md_cell_length_c_average__bohr>{0})".format(self.regexs.regex_f)),
                        SM( " CELL ANGLS\[deg\]              =\s+(?P<x_cp2k_md_cell_angle_a_instantaneous__deg>{0})\s+(?P<x_cp2k_md_cell_angle_b_instantaneous__deg>{0})\s+(?P<x_cp2k_md_cell_angle_c_instantaneous__deg>{0})".format(self.regexs.regex_f)),
                        SM( " AVE. CELL ANGLS\[deg\]         =\s+(?P<x_cp2k_md_cell_angle_a_average__deg>{0})\s+(?P<x_cp2k_md_cell_angle_b_average__deg>{0})\s+(?P<x_cp2k_md_cell_angle_c_average__deg>{0})".format(self.regexs.regex_f)),
                    ],
                    adHoc=self.adHoc_save_md_quickstep()
                ),
            ]
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
                        self.cm.quickstep_header(),
                    ],
                ),
                self.md,
            ]
        )

    #===========================================================================
    # onClose triggers
    def onClose_x_cp2k_section_md_settings(self, backend, gIndex, section):

        # Ensemble
        sampling = section.get_latest_value("x_cp2k_md_ensemble_type")
        if sampling is not None:
            sampling_map = {
                "NVE": "NVE",
                "NVT": "NVT",
                "NPT_F": "NPT",
                "NPT_I": "NPT",
            }
            sampling = sampling_map.get(sampling)
            if sampling is not None:
                self.ensemble = sampling
                backend.addValue("ensemble_type", sampling)

        # Sampling type
        backend.addValue("sampling_method", "molecular_dynamics")

        # Print frequencies
        self.output_freq = section.get_latest_value("x_cp2k_md_print_frequency")
        self.energy_freq = section.get_latest_value("x_cp2k_md_energies_print_frequency")
        self.coord_freq = section.get_latest_value("x_cp2k_md_coordinates_print_frequency")
        self.velo_freq = section.get_latest_value("x_cp2k_md_velocities_print_frequency")
        self.cell_freq = section.get_latest_value("x_cp2k_md_simulation_cell_print_frequency")

        # Step number
        self.n_steps = section.get_latest_value("x_cp2k_md_number_of_time_steps")

        # Files
        coord_filename = section.get_latest_value("x_cp2k_md_coordinates_filename")
        vel_filename = section.get_latest_value("x_cp2k_md_velocities_filename")
        energies_filename = section.get_latest_value("x_cp2k_md_energies_filename")
        cell_filename = section.get_latest_value("x_cp2k_md_simulation_cell_filename")
        coord_filepath = self.file_service.set_file_id(coord_filename, "coordinates")
        vel_filepath = self.file_service.set_file_id(vel_filename, "velocities")
        cell_filepath = self.file_service.set_file_id(cell_filename, "cell")
        energies_filepath = self.file_service.set_file_id(energies_filename, "energies")

        # Setup trajectory iterator
        traj_format = self.cache_service["trajectory_format"]
        if traj_format is not None and coord_filepath is not None:

            # Use special parsing for CP2K pdb files because they don't follow the proper syntax
            if traj_format == "PDB":
                self.traj_iterator = cp2kparser.generic.csvparsing.iread(coord_filepath, columns=[3, 4, 5], start="CRYST", end="END")
            else:
                try:
                    self.traj_iterator = cp2kparser.generic.configurationreading.iread(coord_filepath)
                except ValueError:
                    pass

        # Setup velocity iterator
        vel_format = self.cache_service["velocity_format"]
        if vel_format is not None and vel_filepath is not None:
            try:
                self.vel_iterator = cp2kparser.generic.configurationreading.iread(vel_filepath)
            except ValueError:
                pass

        # Setup energy file iterator
        if energies_filepath is not None:
            self.energy_iterator = cp2kparser.generic.csvparsing.iread(energies_filepath, columns=[0, 1, 2, 3, 4, 5, 6], comments="#")

        # Setup cell file iterator
        if cell_filepath is not None:
            self.cell_iterator = cp2kparser.generic.csvparsing.iread(cell_filepath, columns=[2, 3, 4, 5, 6, 7, 8, 9, 10], comments="#")

    def onClose_x_cp2k_section_md(self, backend, gIndex, section):

        # Determine the highest print frequency and use that as the number of
        # single configuration calculations
        freqs = {
            "output": [self.output_freq, True],
            "trajectory": [self.coord_freq, True],
            "velocities": [self.velo_freq, True],
            "energies": [self.energy_freq, True],
            "cell": [self.cell_freq, True],
        }

        # See if the files actually exist
        traj_file = self.file_service.get_file_by_id("coordinates")
        if traj_file is None:
            freqs["trajectory"][1] = False
        velocities_file = self.file_service.get_file_by_id("velocities")
        if velocities_file is None:
            freqs["velocities"][1] = False
        energies_file = self.file_service.get_file_by_id("energies")
        if energies_file is None:
            freqs["energies"][1] = False
        cell_file = self.file_service.get_file_by_id("cell")
        if cell_file is None:
            freqs["cell"][1] = False

        # See if we can determine the units
        traj_unit = self.cache_service["trajectory_unit"]
        if traj_unit is None:
            freqs["coordinates"][1] = False
        vel_unit = self.cache_service["velocity_unit"]
        if vel_unit is None:
            freqs["velocities"][1] = False

        # Trajectory print settings
        add_last_traj = False
        add_last_traj_setting = self.cache_service["traj_add_last"]
        if add_last_traj_setting == "NUMERIC" or add_last_traj_setting == "SYMBOLIC":
            add_last_traj = True

        # Velocities print settings
        add_last_vel = False
        add_last_vel_setting = self.cache_service["vel_add_last"]
        if add_last_vel_setting == "NUMERIC" or add_last_vel_setting == "SYMBOLIC":
            add_last_vel = True

        last_step = self.n_steps - 1
        md_steps = section["x_cp2k_section_md_step"]

        frame_sequence_potential_energy = []
        frame_sequence_temperature = []
        frame_sequence_time = []
        frame_sequence_kinetic_energy = []
        frame_sequence_conserved_quantity = []
        frame_sequence_pressure = []

        single_conf_gids = []
        i_md_step = 0
        for i_step in range(self.n_steps + 1):

            sectionGID = backend.openSection("section_single_configuration_calculation")
            systemGID = backend.openSection("section_system")
            single_conf_gids.append(sectionGID)

            # If NPT is run, and the cell file is not available, output the
            # simulation cel only on the first step to section_system
            if i_step == 0 and self.ensemble == "NPT" and self.cell_iterator is None:
                self.cache_service.push_array_values("simulation_cell", unit="angstrom")

            # Trajectory
            if freqs["trajectory"][1] and self.traj_iterator is not None:
                if (i_step + 1) % freqs["trajectory"][0] == 0 or (i_step == last_step and add_last_traj):
                    try:
                        pos = next(self.traj_iterator)
                    except StopIteration:
                        logger.error("Could not get the next geometries from an external file. It seems that the number of optimization steps in the CP2K outpufile doesn't match the number of steps found in the external trajectory file.")
                    else:
                        backend.addArrayValues("atom_positions", pos, unit=traj_unit)

            # Velocities
            if freqs["velocities"][1] and self.vel_iterator is not None:
                if (i_step + 1) % freqs["velocities"][0] == 0 or (i_step == last_step and add_last_vel):
                    try:
                        vel = next(self.vel_iterator)
                    except StopIteration:
                        logger.error("Could not get the next velociies from an external file. It seems that the number of optimization steps in the CP2K outpufile doesn't match the number of steps found in the external velocities file.")
                    else:
                        backend.addArrayValues("atom_velocities", vel, unit=vel_unit)

            # Energy file
            if self.energy_iterator is not None:
                if (i_step + 1) % freqs["energies"][0] == 0:
                    line = next(self.energy_iterator)

                    time = line[1]
                    kinetic_energy = line[2]
                    temperature = line[3]
                    potential_energy = line[4]
                    conserved_quantity = line[5]
                    wall_time = line[6]

                    frame_sequence_time.append(time)
                    frame_sequence_kinetic_energy.append(kinetic_energy)
                    frame_sequence_temperature.append(temperature)
                    frame_sequence_potential_energy.append(potential_energy)
                    frame_sequence_conserved_quantity.append(conserved_quantity)

                    backend.addValue("energy_total", conserved_quantity)
                    backend.addValue("time_calculation", wall_time)

            # Cell file
            if self.cell_iterator is not None:
                if (i_step + 1) % freqs["cell"][0] == 0:
                    line = next(self.cell_iterator)
                    cell = np.reshape(line, (3, 3))
                    self.backend.addArrayValues("simulation_cell", cell, unit="angstrom")
                    # self.cache_service["simulation_cell"] = cell

            # Output file
            if md_steps:
                if (i_step + 1) % freqs["output"][0] == 0:
                    md_step = md_steps[i_md_step]
                    quickstep = self.md_quicksteps[i_md_step]
                    if quickstep is not None:
                        quickstep.add_latest_value("x_cp2k_atom_forces", "atom_forces")
                        quickstep.add_latest_value("x_cp2k_stress_tensor", "stress_tensor")
                        scfGID = backend.openSection("section_scf_iteration")
                        quickstep.add_latest_value(["x_cp2k_section_scf_iteration", "x_cp2k_energy_total_scf_iteration"], "energy_total_scf_iteration")
                        quickstep.add_latest_value(["x_cp2k_section_scf_iteration", "x_cp2k_energy_change_scf_iteration"], "energy_change_scf_iteration")
                        quickstep.add_latest_value(["x_cp2k_section_scf_iteration", "x_cp2k_energy_XC_scf_iteration"], "energy_XC_scf_iteration")
                        backend.closeSection("section_scf_iteration", scfGID)
                    i_md_step += 1
                    pressure = md_step.get_latest_value("x_cp2k_md_pressure_instantaneous")
                    if pressure is not None:
                        frame_sequence_pressure.append(pressure)

            backend.closeSection("section_system", systemGID)
            backend.closeSection("section_single_configuration_calculation", sectionGID)

        # Add the summaries to frame sequence
        frame_sequence_potential_energy = convert_unit(np.array(frame_sequence_potential_energy), "hartree")
        frame_sequence_kinetic_energy = convert_unit(np.array(frame_sequence_kinetic_energy), "hartree")
        frame_sequence_conserved_quantity = convert_unit(np.array(frame_sequence_conserved_quantity), "hartree")
        frame_sequence_time = np.array(frame_sequence_time)
        frame_sequence_temperature = np.array(frame_sequence_temperature)
        frame_sequence_pressure = np.array(frame_sequence_pressure)

        backend.addArrayValues("frame_sequence_potential_energy", frame_sequence_potential_energy)
        backend.addArrayValues("frame_sequence_kinetic_energy", frame_sequence_kinetic_energy)
        backend.addArrayValues("frame_sequence_conserved_quantity", frame_sequence_conserved_quantity)
        backend.addArrayValues("frame_sequence_temperature", frame_sequence_temperature)
        backend.addArrayValues("frame_sequence_time", frame_sequence_time, unit="fs")
        if frame_sequence_pressure.size != 0:
            backend.addArrayValues("frame_sequence_pressure", frame_sequence_pressure)

        # Number of frames
        backend.addValue("number_of_frames_in_sequence", self.n_steps + 1)

        # Reference to sampling method
        backend.addValue("frame_sequence_to_sampling_ref", 0)

        # References to local frames
        backend.addArrayValues("frame_sequence_local_frames_ref", np.array(single_conf_gids))

        # Temperature stats
        mean_temp = frame_sequence_temperature.mean()
        std_temp = frame_sequence_temperature.std()
        backend.addArrayValues("frame_sequence_temperature_stats", np.array([mean_temp, std_temp]))

        # Potential energy stats
        mean_pot = frame_sequence_potential_energy.mean()
        std_pot = frame_sequence_potential_energy.std()
        backend.addArrayValues("frame_sequence_potential_energy_stats", np.array([mean_pot, std_pot]))

        # Kinetic energy stats
        mean_kin = frame_sequence_kinetic_energy.mean()
        std_kin = frame_sequence_kinetic_energy.std()
        backend.addArrayValues("frame_sequence_kinetic_energy_stats", np.array([mean_kin, std_kin]))

        # Conserved quantity stats
        mean_cons = frame_sequence_conserved_quantity.mean()
        std_cons = frame_sequence_conserved_quantity.std()
        backend.addArrayValues("frame_sequence_conserved_quantity_stats", np.array([mean_cons, std_cons]))

        # Pressure stats
        if frame_sequence_pressure.size != 0:
            mean_pressure = frame_sequence_pressure.mean()
            std_pressure = frame_sequence_pressure.std()
            backend.addArrayValues("frame_sequence_pressure_stats", np.array([mean_pressure, std_pressure]))

    #===========================================================================
    # adHoc functions
    def adHoc_save_md_quickstep(self):
        def wrapper(parser):
            section_managers = parser.backend.sectionManagers
            section_run_manager = section_managers["section_run"]
            section_run = section_run_manager.openSections[0]
            quickstep = section_run.get_latest_value("x_cp2k_section_quickstep_calculation")
            self.md_quicksteps.append(quickstep)
        return wrapper
