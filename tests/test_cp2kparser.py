#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
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

import pytest

from nomad.datamodel import EntryArchive
from cp2kparser import CP2KParser


@pytest.fixture(scope='module')
def parser():
    return CP2KParser()


def test_single_point(parser):
    archive = EntryArchive()
    parser.parse('tests/data/single_point/si_bulk8.out', archive, None)

    sec_run = archive.section_run[0]
    assert sec_run.program_version == 'CP2K version 2.6.2'
    assert len(sec_run.x_cp2k_section_dbcsr[0]) == 9
    assert sec_run.x_cp2k_section_global_settings[0].x_cp2k_run_type == 'ENERGY_FORCE'

    assert sec_run.x_cp2k_section_startinformation[0].x_cp2k_start_id == 8212
    assert sec_run.x_cp2k_section_end_information[0].x_cp2k_end_time == '2016-02-08 22:11:17.875'
    assert sec_run.x_cp2k_section_program_information[0].x_cp2k_svn_revision == 15893
    assert pytest.approx(sec_run.section_basis_set_cell_dependent[0].basis_set_planewave_cutoff.magnitude, 6.53961708e-16)
    assert sec_run.section_basis_set_atom_centered[0].basis_set_atom_centered_short_name == 'DZVP-GTH-PADE'
    assert len(sec_run.x_cp2k_section_quickstep_calculation) == 1

    sec_input = sec_run.x_cp2k_section_input[0]
    assert sec_input.x_cp2k_section_input_GLOBAL[0].x_cp2k_input_GLOBAL_PROJECT_NAME == 'Si_bulk8'
    sec_force_eval_dft = sec_input.x_cp2k_section_input_FORCE_EVAL[0].x_cp2k_section_input_FORCE_EVAL_DFT[0]
    assert sec_force_eval_dft.x_cp2k_section_input_FORCE_EVAL_DFT_SCF[0].x_cp2k_input_FORCE_EVAL_DFT_SCF_EPS_SCF == '1.0E-7'

    sec_method = sec_run.section_method[0]
    assert pytest.approx(sec_method.scf_threshold_energy_change.magnitude, 4.35974472220717e-25)
    assert sec_method.section_XC_functionals[0].XC_functional_name == 'LDA_XC_TETER93'
    sec_qs_settings = sec_method.x_cp2k_section_quickstep_settings[0]
    assert sec_qs_settings.x_cp2k_planewave_cutoff == 150.
    sec_atom_kind = sec_qs_settings.x_cp2k_section_atomic_kinds[0].x_cp2k_section_atomic_kind[0]
    assert sec_atom_kind.x_cp2k_kind_number_of_atoms == '8'
    assert sec_atom_kind.x_cp2k_section_kind_basis_set[0].x_cp2k_basis_set_norm_type == 2
    assert sec_qs_settings.x_cp2k_section_total_numbers[0].x_cp2k_cartesian_basis_functions == 112
    assert sec_qs_settings.x_cp2k_section_maximum_angular_momentum[0].x_cp2k_orbital_basis_functions == 2
    assert sec_method.section_method_atom_kind[0].method_atom_kind_atom_number == 14

    assert len(sec_run.section_single_configuration_calculation) == 1
    sec_scc = sec_run.section_single_configuration_calculation[0]
    assert pytest.approx(sec_scc.energy_total.magnitude, -1.36450791e-16)
    assert pytest.approx(sec_scc.atom_forces[4][1].magnitude, -8.2387235e-16)
    assert len(sec_scc.section_scf_iteration) == 10
    assert pytest.approx(sec_scc.section_scf_iteration[1].energy_total_scf_iteration.magnitude, -1.35770357e-16)

    sec_system = sec_run.section_system[0]
    assert sec_system.atom_labels == ['Si'] * 8
    assert pytest.approx(sec_system.atom_positions[6][2].magnitude, 4.073023e-10)
    assert pytest.approx(sec_system.lattice_vectors[2][2].magnitude, 5.431e-10)
    assert False not in sec_system.configuration_periodic_dimensions

    assert sec_run.section_sampling_method[0].sampling_method == 'single_point'


def test_geometry_optimization(parser):
    archive = EntryArchive()
    parser.parse('tests/data/geometry_optimization/H2O.out', archive, None)

    assert len(archive.section_run[0].x_cp2k_section_quickstep_calculation) == 101

    sec_sampling = archive.section_run[0].section_sampling_method[0]
    assert sec_sampling.geometry_optimization_method == 'conjugate gradient'
    sec_opt = sec_sampling.x_cp2k_section_geometry_optimization[0]
    assert len(sec_opt.x_cp2k_section_geometry_optimization_step) == 11
    assert pytest.approx(sec_opt.x_cp2k_section_geometry_optimization_step[2].x_cp2k_optimization_rms_gradient, 1.0992366882757706e-10)
    assert pytest.approx(sec_opt.x_cp2k_section_geometry_optimization_step[-1].x_cp2k_optimization_energy_change, -2.306304958047593e-25)

    sec_sccs = archive.section_run[0].section_single_configuration_calculation
    assert len(sec_sccs) == 13
    assert pytest.approx(sec_sccs[7].energy_XC.magnitude, -1.79928366e-17)
    assert len(sec_sccs[2].section_scf_iteration) == 7
    assert pytest.approx(sec_sccs[11].section_scf_iteration[-1].energy_total_scf_iteration.magnitude, -7.48333145e-17)

    sec_systems = archive.section_run[0].section_system
    assert len(sec_systems) == 13
    assert pytest.approx(sec_systems[6].atom_positions[1][1].magnitude, 2.25671575e-10)


def test_molecular_dynamics(parser):
    archive = EntryArchive()
    parser.parse('tests/data/molecular_dynamics/H2O-32.out', archive, None)

    sec_sampling = archive.section_run[0].section_sampling_method[0]
    assert sec_sampling.ensemble_type == 'NVE'
    assert sec_sampling.x_cp2k_section_md_settings[0].x_cp2k_md_print_frequency == 1

    sec_sccs = archive.section_run[0].section_single_configuration_calculation
    assert len(sec_sccs) == 12
    assert len(sec_sccs[6].section_scf_iteration) == 7
    assert pytest.approx(sec_sccs[3].energy_total.magnitude, -1.49661312e-16)
    assert pytest.approx(sec_sccs[10].x_cp2k_section_md_step[0].x_cp2k_md_kinetic_energy_instantaneous, 2.34172483e-20)

    sec_systems = archive.section_run[0].section_system
    assert len(sec_systems) == 12
    assert pytest.approx(sec_systems[5].atom_positions[4][0].magnitude, 5.8374765e-11)
