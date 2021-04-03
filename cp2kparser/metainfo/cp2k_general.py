#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD.
# See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import numpy as np            # pylint: disable=unused-import
import typing                 # pylint: disable=unused-import
from nomad.metainfo import (  # pylint: disable=unused-import
    MSection, MCategory, Category, Package, Quantity, Section, SubSection, SectionProxy,
    Reference
)
from nomad.metainfo.legacy import LegacyDefinition

from nomad.datamodel.metainfo import public

m_package = Package(
    name='cp2k_general_nomadmetainfo_json',
    description='None',
    a_legacy=LegacyDefinition(name='cp2k.general.nomadmetainfo.json'))


class x_cp2k_section_restart_information(MSection):
    '''
    Contains restart information for this calculation.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_restart_information'))

    x_cp2k_restart_file_name = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the restart file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_restart_file_name'))

    x_cp2k_restarted_quantity_name = Quantity(
        type=str,
        shape=[],
        description='''
        Name of a restarted quantity.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_restarted_quantity_name'))


class x_cp2k_section_dbcsr(MSection):
    '''
    The DBCSR (Distributed Block Compressed Sparse Row) information.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_dbcsr'))

    x_cp2k_dbcsr_multiplication_driver = Quantity(
        type=str,
        shape=[],
        description='''
        DBCSR Multiplication driver
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_multiplication_driver'))

    x_cp2k_dbcsr_multrec_recursion_limit = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        DBCSR Multrec recursion limit
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_multrec_recursion_limit'))

    x_cp2k_dbcsr_multiplication_stack_size = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        DBCSR Multiplication stack size.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_multiplication_stack_size'))

    x_cp2k_dbcsr_multiplication_size_stacks = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        DBCSR Multiplication size of stacks.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_multiplication_size_stacks'))

    x_cp2k_dbcsr_use_subcommunicators = Quantity(
        type=str,
        shape=[],
        description='''
        Boolean indicating if subcommunicators are used.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_use_subcommunicators'))

    x_cp2k_dbcsr_use_mpi_combined_types = Quantity(
        type=str,
        shape=[],
        description='''
        Boolean indicating if MPI combined types are used.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_use_mpi_combined_types'))

    x_cp2k_dbcsr_use_mpi_memory_allocation = Quantity(
        type=str,
        shape=[],
        description='''
        Boolean indicating if MPI memory allocation is used.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_use_mpi_memory_allocation'))

    x_cp2k_dbcsr_use_communication_thread = Quantity(
        type=str,
        shape=[],
        description='''
        Boolean indicating if communication thread is used.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_use_communication_thread'))

    x_cp2k_dbcsr_communication_thread_load = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Load of the communication thread.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_dbcsr_communication_thread_load'))


class x_cp2k_section_global_settings(MSection):
    '''
    Global settings for this calculation.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_global_settings'))

    x_cp2k_basis_set_filename = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the basis set file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_basis_set_filename'))

    x_cp2k_coordinate_filename = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the coordinate file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_coordinate_filename'))

    x_cp2k_geminal_filename = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the geminal file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_geminal_filename'))

    x_cp2k_mm_potential_filename = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the MM potential file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_mm_potential_filename'))

    x_cp2k_potential_filename = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the potential file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_potential_filename'))

    x_cp2k_method_name = Quantity(
        type=str,
        shape=[],
        description='''
        The method name for this run.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_method_name'))

    x_cp2k_preferred_fft_library = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the preferred FFT library.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_preferred_fft_library'))

    x_cp2k_preferred_diagonalization_library = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the preferred diagonalization library.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_preferred_diagonalization_library'))

    x_cp2k_run_type = Quantity(
        type=str,
        shape=[],
        description='''
        The run type for this calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_run_type'))


class x_cp2k_section_geometry_optimization_energy_reevaluation(MSection):
    '''
    Information for the energy re-evaluation at the end of an optimization procedure.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_geometry_optimization_energy_reevaluation'))


class x_cp2k_section_geometry_optimization_step(MSection):
    '''
    Contains information about the geometry optimization process for every optimization
    step.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_geometry_optimization_step'))

    x_cp2k_optimization_energy_change = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Energy change for this optimization step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_energy_change'))

    x_cp2k_optimization_energy_decrease = Quantity(
        type=str,
        shape=[],
        description='''
        Whether there has been energy decrease. YES or NO.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_energy_decrease'))

    x_cp2k_optimization_energy = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Energy for this optimization step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_energy'))

    x_cp2k_optimization_gradient_convergence_limit = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Convergence criterium for the maximum force component of the current
        configuration.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_gradient_convergence_limit'))

    x_cp2k_optimization_max_gradient_convergence = Quantity(
        type=str,
        shape=[],
        description='''
        Whether there is convergence in max gradient. YES or NO.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_max_gradient_convergence'))

    x_cp2k_optimization_max_gradient = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Max gradient for this optimization step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_max_gradient'))

    x_cp2k_optimization_max_step_size = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Maximum step size for this optimization step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_max_step_size'))

    x_cp2k_optimization_method = Quantity(
        type=str,
        shape=[],
        description='''
        Optimization method for this step
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_method'))

    x_cp2k_optimization_rms_gradient_convergence = Quantity(
        type=str,
        shape=[],
        description='''
        Whether there is convergence in rms gradient. YES or NO.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_rms_gradient_convergence'))

    x_cp2k_optimization_rms_gradient = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        RMS gradient for this optimization step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_rms_gradient'))

    x_cp2k_optimization_rms_step_size_convergence = Quantity(
        type=str,
        shape=[],
        description='''
        Whether there is convergence in rms step size. YES or NO.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_rms_step_size_convergence'))

    x_cp2k_optimization_rms_step_size = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        RMS step size for this optimization step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_rms_step_size'))

    x_cp2k_optimization_step_size_convergence_limit = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Convergence criterium for the maximum geometry change between the current and the
        last optimizer iteration.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_step_size_convergence_limit'))

    x_cp2k_optimization_step_size_convergence = Quantity(
        type=str,
        shape=[],
        description='''
        Whether there is convergence in step size. YES or NO.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_step_size_convergence'))

    x_cp2k_optimization_used_time = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Time used for this optimization step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_optimization_used_time'))


class x_cp2k_section_geometry_optimization(MSection):
    '''
    CP2K geometry optimization information.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_geometry_optimization'))

    x_cp2k_section_geometry_optimization_energy_reevaluation = SubSection(
        sub_section=SectionProxy('x_cp2k_section_geometry_optimization_energy_reevaluation'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_geometry_optimization_energy_reevaluation'))

    x_cp2k_section_geometry_optimization_step = SubSection(
        sub_section=SectionProxy('x_cp2k_section_geometry_optimization_step'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_geometry_optimization_step'))


class x_cp2k_section_maximum_angular_momentum(MSection):
    '''
    Contains the maximum angular momentum values used in the calculation.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_maximum_angular_momentum'))

    x_cp2k_local_part_of_gth_pseudopotential = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Maximum angular momentum of the local part of the GTH pseudopotential.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_local_part_of_gth_pseudopotential'))

    x_cp2k_non_local_part_of_gth_pseudopotential = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Maximum angular momentum of the non-local part of the GTH pseudopotential.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_non_local_part_of_gth_pseudopotential'))

    x_cp2k_orbital_basis_functions = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Maximum angular momentum of orbital basis functions.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_orbital_basis_functions'))


class x_cp2k_section_program_information(MSection):
    '''
    Contains information about the software version used for this run.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_program_information'))

    x_cp2k_input_filename = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the CP2K input file that produced this calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_input_filename'))

    x_cp2k_program_compilation_datetime = Quantity(
        type=str,
        shape=[],
        description='''
        The time when this program was compiled.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_program_compilation_datetime'))

    x_cp2k_svn_revision = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The SVN revision number.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_svn_revision'))


class x_cp2k_section_quickstep_calculation(MSection):
    '''
    Section for a CP2K QuickStep calculation.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_quickstep_calculation'))

    x_cp2k_atom_forces = Quantity(
        type=np.dtype(np.float64),
        shape=['number_of_atoms', 3],
        unit='newton',
        description='''
        Forces acting on the atoms in this Quickstep calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_atom_forces'))

    x_cp2k_electronic_kinetic_energy = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        unit='joule',
        description='''
        Self-consistent electronic kinetic energy calculated with Quickstep
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_electronic_kinetic_energy'))

    x_cp2k_energy_total = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        unit='joule',
        description='''
        Value of the total energy (nuclei + electrons) calculated with Quickstep.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_energy_total'))

    x_cp2k_quickstep_converged = Quantity(
        type=bool,
        shape=[],
        description='''
        Boolean indicating whether the quickstep SCF cycle converged or not.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_quickstep_converged'))

    x_cp2k_section_scf_iteration = SubSection(
        sub_section=SectionProxy('x_cp2k_section_scf_iteration'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_scf_iteration'))

    x_cp2k_section_stress_tensor = SubSection(
        sub_section=SectionProxy('x_cp2k_section_stress_tensor'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_stress_tensor'))


class x_cp2k_section_scf_iteration(MSection):
    '''
    Section for a CP2K QuickStep SCF iteration.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_scf_iteration'))

    x_cp2k_energy_change_scf_iteration = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        unit='joule',
        description='''
        At each self-consistent field (SCF) iteration, change of total energy with respect
        to the previous SCF iteration.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_energy_change_scf_iteration'))

    x_cp2k_energy_total_scf_iteration = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        unit='joule',
        description='''
        Total electronic energy calculated with XC_method during the self-consistent field
        (SCF) iterations.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_energy_total_scf_iteration'))

    x_cp2k_energy_XC_scf_iteration = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        unit='joule',
        description='''
        Exchange-correlation (XC) energy during the self-consistent field (SCF) iteration.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_energy_XC_scf_iteration'))


class x_cp2k_section_startinformation(MSection):
    '''
    Contains information about the starting conditions for this run.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_startinformation'))

    x_cp2k_start_time = Quantity(
        type=str,
        shape=[],
        description='''
        The starting time for this run.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_start_time'))

    x_cp2k_start_host = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the host machine this calculation started on.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_start_host'))

    x_cp2k_start_user = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the user at the start of the calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_start_user'))

    x_cp2k_start_id = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The process id at the start of this run.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_start_id'))

    x_cp2k_start_path = Quantity(
        type=str,
        shape=[],
        description='''
        The path where this calculation started.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_start_path'))


class x_cp2k_section_end_information(MSection):
    '''
    Contains information about the ending conditions for this run.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_end_information'))

    x_cp2k_end_time = Quantity(
        type=str,
        shape=[],
        description='''
        The ending time for this run.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_end_time'))

    x_cp2k_end_host = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the host machine this calculation ended on.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_end_host'))

    x_cp2k_end_user = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the user at the end of the calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_end_user'))

    x_cp2k_end_id = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The process id at the end of this run.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_end_id'))

    x_cp2k_end_path = Quantity(
        type=str,
        shape=[],
        description='''
        The path where this calculation ended.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_end_path'))


class x_cp2k_section_stress_tensor(MSection):
    '''
    Section for stress tensor information.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_stress_tensor'))

    x_cp2k_stress_tensor_determinant = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        The determinant of the stress tensor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_stress_tensor_determinant'))

    x_cp2k_stress_tensor_eigenvalues = Quantity(
        type=np.dtype(np.float64),
        shape=[3],
        description='''
        The eigenvalues of the stress tensor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_stress_tensor_eigenvalues'))

    x_cp2k_stress_tensor_eigenvectors = Quantity(
        type=np.dtype(np.float64),
        shape=[3, 3],
        description='''
        The eigenvectors of the stress tensor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_stress_tensor_eigenvectors'))

    x_cp2k_stress_tensor_one_third_of_trace = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        1/3 of the trace of the stress tensor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_stress_tensor_one_third_of_trace'))

    x_cp2k_stress_tensor = Quantity(
        type=np.dtype(np.float64),
        shape=[3, 3],
        unit='pascal',
        description='''
        A final value of the stress tensor in a Quickstep calculation
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_stress_tensor'))


class x_cp2k_section_total_numbers(MSection):
    '''
    The total number of different entities in the calculation.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_total_numbers'))

    x_cp2k_atomic_kinds = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The number of atomic kinds in the calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_atomic_kinds'))

    x_cp2k_atoms = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The number of atoms in the calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_atoms'))

    x_cp2k_cartesian_basis_functions = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The number of Cartesian basis functions.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_cartesian_basis_functions'))

    x_cp2k_primitive_cartesian_functions = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The number of primitive Cartesian functions.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_primitive_cartesian_functions'))

    x_cp2k_shell_sets = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The number of shell sets in the calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_shell_sets'))

    x_cp2k_shells = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The number of shells.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_shells'))

    x_cp2k_spherical_basis_functions = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The number of Spherical basis functions.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_spherical_basis_functions'))


class x_cp2k_section_md(MSection):
    '''
    CP2K Molecular Dynamics information.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_md'))

    x_cp2k_section_md_step = SubSection(
        sub_section=SectionProxy('x_cp2k_section_md_step'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_md_step'))


class x_cp2k_section_md_settings(MSection):
    '''
    Settings for CP2K Molecular Dynamics.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_md_settings'))

    x_cp2k_md_ensemble_type = Quantity(
        type=str,
        shape=[],
        description='''
        The ensemble type in molecular dynamics.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_ensemble_type'))

    x_cp2k_md_time_step = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Time step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_time_step'))

    x_cp2k_md_target_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Thermostat target temperature.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_target_temperature'))

    x_cp2k_md_target_temperature_tolerance = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Target temperature tolerance.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_target_temperature_tolerance'))

    x_cp2k_md_print_frequency = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The print frequency of molecular dynamics information in the CP2K output file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_print_frequency'))

    x_cp2k_md_coordinates_print_frequency = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Print frequency for the coordinate file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_coordinates_print_frequency'))

    x_cp2k_md_coordinates_filename = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the coordinate file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_coordinates_filename'))

    x_cp2k_md_velocities_print_frequency = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Print frequency for the velocities file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_velocities_print_frequency'))

    x_cp2k_md_velocities_filename = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the velocities file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_velocities_filename'))

    x_cp2k_md_energies_print_frequency = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Print frequency for the energies file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_energies_print_frequency'))

    x_cp2k_md_energies_filename = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the energies file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_energies_filename'))

    x_cp2k_md_dump_print_frequency = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Print frequency for the dump file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_dump_print_frequency'))

    x_cp2k_md_dump_filename = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the dump file.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_dump_filename'))

    x_cp2k_md_target_pressure = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Target pressure for the barostat.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_target_pressure'))

    x_cp2k_md_barostat_time_constant = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Barostat time constant.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_barostat_time_constant'))

    x_cp2k_md_simulation_cell_print_frequency = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Simulation cell print frequency.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_simulation_cell_print_frequency'))

    x_cp2k_md_simulation_cell_filename = Quantity(
        type=str,
        shape=[],
        description='''
        Simulation cell filename.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_simulation_cell_filename'))

    x_cp2k_md_number_of_time_steps = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Number of requested time steps in molecular dynamics.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_number_of_time_steps'))


class x_cp2k_section_md_step(MSection):
    '''
    Information from MD step.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_md_step'))

    x_cp2k_md_potential_energy_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous potential energy in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_potential_energy_instantaneous'))

    x_cp2k_md_potential_energy_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average potential energy for an MD step. Averaged over this and the previous
        steps.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_potential_energy_average'))

    x_cp2k_md_kinetic_energy_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous kinetic energy in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_kinetic_energy_instantaneous'))

    x_cp2k_md_kinetic_energy_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average kinetic energy in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_kinetic_energy_average'))

    x_cp2k_md_energy_drift_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous energy drift in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_energy_drift_instantaneous'))

    x_cp2k_md_energy_drift_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average kinetic energy in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_energy_drift_average'))

    x_cp2k_md_temperature_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous temperature in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_temperature_instantaneous'))

    x_cp2k_md_temperature_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average temperature in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_temperature_average'))

    x_cp2k_md_barostat_temperature_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous barostat temperature in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_barostat_temperature_instantaneous'))

    x_cp2k_md_barostat_temperature_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average barostat temperature in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_barostat_temperature_average'))

    x_cp2k_md_pressure_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous pressure in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_pressure_instantaneous'))

    x_cp2k_md_pressure_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average pressure in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_pressure_average'))

    x_cp2k_md_cpu_time_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous CPU time for this step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cpu_time_instantaneous'))

    x_cp2k_md_cpu_time_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average CPU time for this step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cpu_time_average'))

    x_cp2k_md_step_number = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Step number.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_step_number'))

    x_cp2k_md_time = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Simulation time for this step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_time'))

    x_cp2k_md_conserved_quantity = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Conserved quantity for this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_conserved_quantity'))

    x_cp2k_md_volume_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell volume in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_volume_instantaneous'))

    x_cp2k_md_volume_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell volume in an MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_volume_average'))

    x_cp2k_md_cell_length_a_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell vector a length in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_a_instantaneous'))

    x_cp2k_md_cell_length_a_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell vector a length in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_a_average'))

    x_cp2k_md_cell_length_b_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell vector b length in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_b_instantaneous'))

    x_cp2k_md_cell_length_b_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell vector b length in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_b_average'))

    x_cp2k_md_cell_length_c_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell vector c length in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_c_instantaneous'))

    x_cp2k_md_cell_length_c_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell vector c length in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_c_average'))

    x_cp2k_md_cell_length_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[3],
        description='''
        Instantaneous cell vector lengths in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_c_instantaneous'))

    x_cp2k_md_cell_length_average = Quantity(
        type=np.dtype(np.float64),
        shape=[3],
        description='''
        Average cell vector lengths in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_length_c_average'))

    x_cp2k_md_cell_angle_a_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell vector a angle in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_a_instantaneous'))

    x_cp2k_md_cell_angle_a_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell vector a angle in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_a_average'))

    x_cp2k_md_cell_angle_b_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell vector b angle in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_b_instantaneous'))

    x_cp2k_md_cell_angle_b_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell vector b angle in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_b_average'))

    x_cp2k_md_cell_angle_c_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell vector c angle in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_c_instantaneous'))

    x_cp2k_md_cell_angle_c_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell vector c angle in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_c_average'))

    x_cp2k_md_cell_angle_instantaneous = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Instantaneous cell vector angles in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_c_instantaneous'))

    x_cp2k_md_cell_angle_average = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Average cell vector angles in this MD step.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_md_cell_angle_c_average'))


class x_cp2k_section_quickstep_settings(MSection):
    '''
    Quickstep settings.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_quickstep_settings'))

    x_cp2k_planewave_cutoff = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        The plane-wave cutoff for the auxiliary basis.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_planewave_cutoff'))

    x_cp2k_spin_restriction = Quantity(
        type=str,
        shape=[],
        description='''
        Indicates the restriction applied for the spin (e.g. RKS).
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_spin_restriction'))

    x_cp2k_quickstep_method = Quantity(
        type=str,
        shape=[],
        description='''
        The method used for the Quickstep calculations (GPW, GAPW).
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_quickstep_method'))

    x_cp2k_section_maximum_angular_momentum = SubSection(
        sub_section=SectionProxy('x_cp2k_section_maximum_angular_momentum'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_maximum_angular_momentum'))

    x_cp2k_section_total_numbers = SubSection(
        sub_section=SectionProxy('x_cp2k_section_total_numbers'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_total_numbers'))

    x_cp2k_section_atomic_kinds = SubSection(
        sub_section=SectionProxy('x_cp2k_section_atomic_kinds'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_atomic_kinds'))


class x_cp2k_section_atomic_kinds(MSection):
    '''
    Information about all the atomic kinds in this Quickstep calculation.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_atomic_kinds'))

    x_cp2k_section_atomic_kind = SubSection(
        sub_section=SectionProxy('x_cp2k_section_atomic_kind'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_atomic_kind'))


class x_cp2k_section_vdw_settings(MSection):
    '''
    Van der Waals settings.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_settings'))

    x_cp2k_vdw_type = Quantity(
        type=str,
        shape=[],
        description='''
        Type of the van der Waals method.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_type'))

    x_cp2k_vdw_name = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the van der Waals method.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_name'))

    x_cp2k_vdw_bj_damping_name = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the BJ damping method.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_bj_damping_name'))

    x_cp2k_vdw_cutoff_radius = Quantity(
        type=str,
        shape=[],
        description='''
        Cutoff radius of the van der Waals method.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_cutoff_radius'))

    x_cp2k_section_vdw_d2_settings = SubSection(
        sub_section=SectionProxy('x_cp2k_section_vdw_d2_settings'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_d2_settings'))

    x_cp2k_section_vdw_d3_settings = SubSection(
        sub_section=SectionProxy('x_cp2k_section_vdw_d3_settings'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_d3_settings'))


class x_cp2k_section_vdw_d2_settings(MSection):
    '''
    D2 settings.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_d2_settings'))

    x_cp2k_vdw_scaling_factor = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Scaling factor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_scaling_factor'))

    x_cp2k_vdw_damping_factor = Quantity(
        type=str,
        shape=[],
        description='''
        Exponential damping prefactor for the van der Waals method.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_damping_factor'))

    x_cp2k_section_vdw_element_settings = SubSection(
        sub_section=SectionProxy('x_cp2k_section_vdw_element_settings'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_element_settings'))


class x_cp2k_section_vdw_element_settings(MSection):
    '''
    Contains element-specific Van der Waals settings.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_element_settings'))

    x_cp2k_vdw_parameter_element_name = Quantity(
        type=str,
        shape=[],
        description='''
        Name of the element.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_parameter_element_name'))

    x_cp2k_vdw_parameter_c6 = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        C6 parameter.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_parameter_c6'))

    x_cp2k_vdw_parameter_radius = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Radius parameter.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_parameter_radius'))


class x_cp2k_section_vdw_d3_settings(MSection):
    '''
    D3 settings.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_d3_settings'))

    x_cp2k_vdw_s6_scaling_factor = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        S6 scaling factor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_s6_scaling_factor'))

    x_cp2k_vdw_sr6_scaling_factor = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        SR6 scaling factor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_sr6_scaling_factor'))

    x_cp2k_vdw_s8_scaling_factor = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        S8 scaling factor.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_s8_scaling_factor'))

    x_cp2k_vdw_cn_cutoff = Quantity(
        type=np.dtype(np.float64),
        shape=[],
        description='''
        Cutoff for CN calculation.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_vdw_cn_cutoff'))


class x_cp2k_section_atomic_kind(MSection):
    '''
    Information one atomic kind.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_atomic_kind'))

    x_cp2k_kind_number = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        The atomic kind number. For each element there may be multiple kinds specified.
        This number differentiates them. Not the atomic number.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_kind_number'))

    x_cp2k_kind_label = Quantity(
        type=str,
        shape=[],
        description='''
        The label for this atomic kind.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_kind_label'))

    x_cp2k_kind_number_of_atoms = Quantity(
        type=str,
        shape=[],
        description='''
        The number of atoms with this kind.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_kind_number_of_atoms'))

    x_cp2k_section_kind_basis_set = SubSection(
        sub_section=SectionProxy('x_cp2k_section_kind_basis_set'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_kind_basis_set'))


class x_cp2k_section_kind_basis_set(MSection):
    '''
    Description of the basis set used for this kind.
    '''

    m_def = Section(validate=False, a_legacy=LegacyDefinition(name='x_cp2k_section_kind_basis_set'))

    x_cp2k_kind_basis_set_name = Quantity(
        type=str,
        shape=[],
        description='''
        The name of the orbital basis set used for this kind.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_kind_basis_set_name'))

    x_cp2k_basis_set_number_of_orbital_shell_sets = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Number of orbital shell sets.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_basis_set_number_of_orbital_shell_sets'))

    x_cp2k_basis_set_number_of_orbital_shells = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Number of orbital shells.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_basis_set_number_of_orbital_shells'))

    x_cp2k_basis_set_number_of_primitive_cartesian_functions = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Number of primitive Cartesian functions.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_basis_set_number_of_primitive_cartesian_functions'))

    x_cp2k_basis_set_number_of_cartesian_basis_functions = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Number of Cartesian basis functions.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_basis_set_number_of_cartesian_basis_functions'))

    x_cp2k_basis_set_number_of_spherical_basis_functions = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Number of spherical basis functions.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_basis_set_number_of_spherical_basis_functions'))

    x_cp2k_basis_set_norm_type = Quantity(
        type=np.dtype(np.int32),
        shape=[],
        description='''
        Norm type.
        ''',
        a_legacy=LegacyDefinition(name='x_cp2k_basis_set_norm_type'))


class section_run(public.section_run):

    m_def = Section(validate=False, extends_base_section=True, a_legacy=LegacyDefinition(name='section_run'))

    x_cp2k_section_restart_information = SubSection(
        sub_section=SectionProxy('x_cp2k_section_restart_information'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_restart_information'))

    x_cp2k_section_dbcsr = SubSection(
        sub_section=SectionProxy('x_cp2k_section_dbcsr'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_dbcsr'))

    x_cp2k_section_global_settings = SubSection(
        sub_section=SectionProxy('x_cp2k_section_global_settings'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_global_settings'))

    x_cp2k_section_program_information = SubSection(
        sub_section=SectionProxy('x_cp2k_section_program_information'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_program_information'))

    x_cp2k_section_quickstep_calculation = SubSection(
        sub_section=SectionProxy('x_cp2k_section_quickstep_calculation'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_quickstep_calculation'))

    x_cp2k_section_startinformation = SubSection(
        sub_section=SectionProxy('x_cp2k_section_startinformation'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_startinformation'))

    x_cp2k_section_end_information = SubSection(
        sub_section=SectionProxy('x_cp2k_section_end_information'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_end_information'))


class section_frame_sequence(public.section_frame_sequence):

    m_def = Section(validate=False, extends_base_section=True, a_legacy=LegacyDefinition(name='section_frame_sequence'))

    x_cp2k_section_geometry_optimization = SubSection(
        sub_section=SectionProxy('x_cp2k_section_geometry_optimization'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_geometry_optimization'))

    x_cp2k_section_md = SubSection(
        sub_section=SectionProxy('x_cp2k_section_md'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_md'))


class section_sampling_method(public.section_sampling_method):

    m_def = Section(validate=False, extends_base_section=True, a_legacy=LegacyDefinition(name='section_sampling_method'))

    x_cp2k_section_md_settings = SubSection(
        sub_section=SectionProxy('x_cp2k_section_md_settings'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_md_settings'))

    x_cp2k_section_geometry_optimization = SubSection(
        sub_section=SectionProxy('x_cp2k_section_geometry_optimization'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_geometry_optimization'))


class section_method(public.section_method):

    m_def = Section(validate=False, extends_base_section=True, a_legacy=LegacyDefinition(name='section_method'))

    x_cp2k_section_quickstep_settings = SubSection(
        sub_section=SectionProxy('x_cp2k_section_quickstep_settings'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_quickstep_settings'))

    x_cp2k_section_vdw_settings = SubSection(
        sub_section=SectionProxy('x_cp2k_section_vdw_settings'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_vdw_settings'))


class section_single_configuration_calculation(public.section_single_configuration_calculation):

    m_def = Section(validate=False, extends_base_section=True, a_legacy=LegacyDefinition(name='section_single_configuration_calculation'))

    x_cp2k_section_md_step = SubSection(
        sub_section=SectionProxy('x_cp2k_section_md_step'),
        repeats=True,
        a_legacy=LegacyDefinition(name='x_cp2k_section_md_step'))


m_package.__init_metainfo__()
