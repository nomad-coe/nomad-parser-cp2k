"""
This is a module for unit testing the CP2K parser. The unit tests are run with
a custom backend that outputs the results directly into native python object for
easier and faster analysis.

Each property that has an enumerable list of different possible options is
assigned a new test class, that should ideally test through all the options.

The properties that can have any value imaginable will be tested only for one
specific case inside a test class that is designed for a certain type of run
(MD, optimization, QM/MM, etc.)
"""
import os
import unittest
import logging
import numpy as np
from cp2kparser import CP2KParser
from nomadcore.local_backend import ParserKeyError
from nomadcore.unit_conversion.unit_conversion import convert_unit


#===============================================================================
def get_results(folder, metainfo_to_keep=None):
    """Get the given result from the calculation in the given folder by using
    the Analyzer in the nomadtoolkit package. Tries to optimize the parsing by
    giving the metainfo_to_keep argument.

    Args:
        folder: The folder relative to the directory of this script where the
            parsed calculation resides.
        metaname: The quantity to extract.
    """
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, folder, "unittest.out")
    parser = CP2KParser(filename, None, debug=True, log_level=logging.CRITICAL)
    results = parser.parse()
    return results


#===============================================================================
def get_result(folder, metaname, optimize=True):
    if optimize:
        results = get_results(folder, None)
    else:
        results = get_results(folder)
    result = results[metaname]
    return result


#===============================================================================
class TestErrors(unittest.TestCase):
    """Test misc. error stuations which may occur during the parsing.
    """
    def test_no_file(self):
        self.assertRaises(IOError, get_result, "errors/no_file", "XC_functional")

    def test_invalid_file(self):
        self.assertRaises(RuntimeError, get_result, "errors/invalid_file", "XC_functional")

    def test_invalid_run_type(self):
        self.assertRaises(KeyError, get_result, "errors/invalid_run_type", "XC_functional")

    def test_unknown_version(self):
        get_result("errors/unknown_version", "XC_functional")

    def test_unknown_input_keyword(self):
        get_result("errors/unknown_input_keyword", "XC_functional")

    def test_unknown_input_section(self):
        get_result("errors/unknown_input_section", "XC_functional")

    def test_unknown_input_section_parameter(self):
        get_result("errors/unknown_input_section_parameter", "XC_functional")


#===============================================================================
class TestXCFunctional(unittest.TestCase):
    """Tests that the XC functionals can be properly parsed.
    """

    def test_pade(self):
        xc = get_result("XC_functional/pade", "XC_functional")
        self.assertEqual(xc, "1*LDA_XC_TETER93")

    def test_lda(self):
        xc = get_result("XC_functional/lda", "XC_functional")
        self.assertEqual(xc, "1*LDA_XC_TETER93")

    def test_blyp(self):
        xc = get_result("XC_functional/blyp", "XC_functional")
        self.assertEqual(xc, "1*GGA_C_LYP+1*GGA_X_B88")

    def test_b3lyp(self):
        xc = get_result("XC_functional/b3lyp", "XC_functional")
        self.assertEqual(xc, "1*HYB_GGA_XC_B3LYP")

    def test_olyp(self):
        xc = get_result("XC_functional/olyp", "XC_functional")
        self.assertEqual(xc, "1*GGA_C_LYP+1*GGA_X_OPTX")

    def test_hcth120(self):
        xc = get_result("XC_functional/hcth120", "XC_functional")
        self.assertEqual(xc, "1*GGA_XC_HCTH_120")

    def test_pbe0(self):
        xc = get_result("XC_functional/pbe0", "XC_functional")
        self.assertEqual(xc, "1*HYB_GGA_XC_PBEH")

    def test_pbe(self):
        xc = get_result("XC_functional/pbe", "XC_functional")
        self.assertEqual(xc, "1*GGA_C_PBE+1*GGA_X_PBE")


#===============================================================================
class TestSCFConvergence(unittest.TestCase):
    """Tests whether the convergence status and number of SCF step can be
    parsed correctly.
    """

    def test_converged(self):
        result = get_result("convergence/converged", "single_configuration_calculation_converged")
        self.assertTrue(result)

    def test_non_converged(self):
        result = get_result("convergence/non_converged", "single_configuration_calculation_converged")
        self.assertFalse(result)


#===============================================================================
class TestForceFiles(unittest.TestCase):
    """Tests that different force files that can be output, can actually be
    found and parsed.
    """

    def test_single_point(self):

        result = get_result("force_file/single_point", "atom_forces")
        expected_result = convert_unit(
            np.array([
                [0.00000000, 0.00000000, 0.00000000],
                [0.00000000, 0.00000001, 0.00000001],
                [0.00000001, 0.00000001, 0.00000000],
                [0.00000001, 0.00000000, 0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
            ]),
            "forceAu"
        )
        self.assertTrue(np.array_equal(result, expected_result))


#===============================================================================
class TestSelfInteractionCorrectionMethod(unittest.TestCase):
    """Tests that the self-interaction correction can be properly parsed.
    """

    def test_no(self):
        sic = get_result("sic/no", "self_interaction_correction_method")
        self.assertEqual(sic, "")

    def test_ad(self):
        sic = get_result("sic/ad", "self_interaction_correction_method")
        self.assertEqual(sic, "SIC_AD")

    def test_explicit_orbitals(self):
        sic = get_result("sic/explicit_orbitals", "self_interaction_correction_method")
        self.assertEqual(sic, "SIC_EXPLICIT_ORBITALS")

    def test_mauri_spz(self):
        sic = get_result("sic/mauri_spz", "self_interaction_correction_method")
        self.assertEqual(sic, "SIC_MAURI_SPZ")

    def test_mauri_us(self):
        sic = get_result("sic/mauri_us", "self_interaction_correction_method")
        self.assertEqual(sic, "SIC_MAURI_US")


#===============================================================================
class TestStressTensorMethods(unittest.TestCase):
    """Tests that the stress tensor can be properly parsed for different
    calculation methods.
    """
    def test_none(self):
        get_results("stress_tensor/none", "section_stress_tensor")

    def test_analytical(self):
        results = get_results("stress_tensor/analytical", ["stress_tensor_method", "stress_tensor"])
        method = results["stress_tensor_method"]
        results["stress_tensor"]
        self.assertEqual(method, "Analytical")

    def test_numerical(self):
        results = get_results("stress_tensor/numerical", ["stress_tensor_method", "stress_tensor"])
        method = results["stress_tensor_method"]
        results["stress_tensor"]
        self.assertEqual(method, "Numerical")

    def test_diagonal_analytical(self):
        results = get_results("stress_tensor/diagonal_analytical", ["stress_tensor_method", "stress_tensor"])
        method = results["stress_tensor_method"]
        results["stress_tensor"]
        self.assertEqual(method, "Diagonal analytical")

    def test_diagonal_numerical(self):
        results = get_results("stress_tensor/diagonal_numerical", ["stress_tensor_method", "stress_tensor"])
        method = results["stress_tensor_method"]
        results["stress_tensor"]
        self.assertEqual(method, "Diagonal numerical")


#===============================================================================
class TestConfigurationPeriodicDimensions(unittest.TestCase):
    """Tests that the self-interaction correction can be properly parsed.
    """

    def test_default(self):
        result = get_result("configuration_periodic_dimensions/default", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((True, True, True))))

    def test_none(self):
        result = get_result("configuration_periodic_dimensions/none", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((False, False, False))))

    def test_x(self):
        result = get_result("configuration_periodic_dimensions/x", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((True, False, False))))

    def test_y(self):
        result = get_result("configuration_periodic_dimensions/y", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((False, True, False))))

    def test_z(self):
        result = get_result("configuration_periodic_dimensions/z", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((False, False, True))))

    def test_xy(self):
        result = get_result("configuration_periodic_dimensions/xy", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((True, True, False))))

    def test_xyz(self):
        result = get_result("configuration_periodic_dimensions/xyz", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((True, True, True))))

    def test_xz(self):
        result = get_result("configuration_periodic_dimensions/xz", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((True, False, True))))

    def test_yz(self):
        result = get_result("configuration_periodic_dimensions/yz", "configuration_periodic_dimensions")
        self.assertTrue(np.array_equal(result, np.array((False, True, True))))


#===============================================================================
class TestEnergyForce(unittest.TestCase):
    """Tests for a CP2K calculation with RUN_TYPE ENERGY_FORCE.
    """

    @classmethod
    def setUpClass(cls):
        cls.results = get_results("energy_force", "section_run")
        # cls.results.print_summary()

    def test_energy_total_scf_iteration(self):
        result = self.results["energy_total_scf_iteration"]
        expected_result = convert_unit(np.array(-32.2320848878), "hartree")
        self.assertTrue(np.array_equal(result[0], expected_result))

    def test_program_name(self):
        result = self.results["program_name"]
        self.assertEqual(result, "CP2K")

    def test_program_compilation_host(self):
        result = self.results["program_compilation_host"]
        self.assertEqual(result, "lenovo700")

    def test_scf_max_iteration(self):
        result = self.results["scf_max_iteration"]
        self.assertEqual(result, 300)

    def test_basis_set(self):
        section_basis_set = self.results["section_basis_set"][0]

        # Basis name
        name = section_basis_set["basis_set_name"]
        self.assertEqual(name, "DZVP-GTH-PADE_PW_150.0")

        # Basis kind
        kind = section_basis_set["basis_set_kind"]
        self.assertEqual(kind, "wavefunction")

        # Cell dependent basis mapping
        cell_basis_mapping = section_basis_set["mapping_section_basis_set_cell_dependent"]
        self.assertEqual(cell_basis_mapping, 0)

        # # Atom centered basis mapping
        atom_basis_mapping = section_basis_set["mapping_section_basis_set_atom_centered"]
        self.assertTrue(np.array_equal(atom_basis_mapping, np.array(8*[0])))

    def test_scf_threshold_energy_change(self):
        result = self.results["scf_threshold_energy_change"]
        self.assertEqual(result, convert_unit(1.00E-07, "hartree"))

    def test_number_of_spin_channels(self):
        result = self.results["number_of_spin_channels"]
        self.assertEqual(result, 1)

    def test_electronic_structure_method(self):
        result = self.results["electronic_structure_method"]
        self.assertEqual(result, "DFT")

    def test_energy_change_scf_iteration(self):
        energy_change = self.results["energy_change_scf_iteration"]
        expected_result = convert_unit(np.array(-3.22E+01), "hartree")
        self.assertTrue(np.array_equal(energy_change[0], expected_result))

    def test_energy_XC_scf_iteration(self):
        result = self.results["energy_XC_scf_iteration"]
        expected_result = convert_unit(np.array(-9.4555961214), "hartree")
        self.assertTrue(np.array_equal(result[0], expected_result))

    def test_energy_total(self):
        result = self.results["energy_total"]
        expected_result = convert_unit(np.array(-31.297885372811074), "hartree")
        self.assertTrue(np.array_equal(result, expected_result))

    def test_electronic_kinetic_energy(self):
        result = self.results["electronic_kinetic_energy"]
        expected_result = convert_unit(np.array(13.31525592466419), "hartree")
        self.assertTrue(np.array_equal(result, expected_result))

    def test_atom_forces(self):
        result = self.results["atom_forces"]
        expected_result = convert_unit(
            np.array([
                [0.00000000, 0.00000000, 0.00000000],
                [0.00000000, 0.00000001, 0.00000001],
                [0.00000001, 0.00000001, 0.00000000],
                [0.00000001, 0.00000000, 0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
                [-0.00000001, -0.00000001, -0.00000001],
            ]),
            "forceAu"
        )
        self.assertTrue(np.array_equal(result, expected_result))

    def test_atom_label(self):
        atom_labels = self.results["atom_labels"]
        expected_labels = np.array(8*["Si"])
        self.assertTrue(np.array_equal(atom_labels, expected_labels))

    def test_simulation_cell(self):
        cell = self.results["simulation_cell"]
        n_vectors = cell.shape[0]
        n_dim = cell.shape[1]
        self.assertEqual(n_vectors, 3)
        self.assertEqual(n_dim, 3)
        expected_cell = convert_unit(np.array([[5.431, 0, 0], [0, 5.431, 0], [0, 0, 5.431]]), "angstrom")
        self.assertTrue(np.array_equal(cell, expected_cell))

    def test_number_of_atoms(self):
        n_atoms = self.results["number_of_atoms"]
        self.assertEqual(n_atoms, 8)

    def test_atom_position(self):
        atom_position = self.results["atom_positions"]
        expected_position = convert_unit(np.array([4.073023, 4.073023, 1.357674]), "angstrom")
        self.assertTrue(np.array_equal(atom_position[-1, :], expected_position))

    def test_x_cp2k_filenames(self):
        input_filename = self.results["x_cp2k_input_filename"]
        expected_input = "si_bulk8.inp"
        self.assertTrue(input_filename, expected_input)

        bs_filename = self.results["x_cp2k_basis_set_filename"]
        expected_bs = "../BASIS_SET"
        self.assertEqual(bs_filename, expected_bs)

        geminal_filename = self.results["x_cp2k_geminal_filename"]
        expected_geminal = "BASIS_GEMINAL"
        self.assertEqual(geminal_filename, expected_geminal)

        potential_filename = self.results["x_cp2k_potential_filename"]
        expected_potential = "../GTH_POTENTIALS"
        self.assertEqual(potential_filename, expected_potential)

        mm_potential_filename = self.results["x_cp2k_mm_potential_filename"]
        expected_mm_potential = "MM_POTENTIAL"
        self.assertEqual(mm_potential_filename, expected_mm_potential)

        coordinate_filename = self.results["x_cp2k_coordinate_filename"]
        expected_coordinate = "__STD_INPUT__"
        self.assertEqual(coordinate_filename, expected_coordinate)

    def test_target_multiplicity(self):
        multiplicity = self.results["spin_target_multiplicity"]
        self.assertEqual(multiplicity, 1)

    def test_total_charge(self):
        charge = self.results["total_charge"]
        self.assertEqual(charge, 0)

    def test_section_basis_set_atom_centered(self):
        basis = self.results["section_basis_set_atom_centered"][0]
        name = basis["basis_set_atom_centered_short_name"]
        number = basis["basis_set_atom_number"]
        self.assertEquals(name, "DZVP-GTH-PADE")
        self.assertEquals(number, 14)

    def test_section_basis_set_cell_dependent(self):
        basis = self.results["section_basis_set_cell_dependent"][0]
        cutoff = basis["basis_set_planewave_cutoff"]
        self.assertEquals(cutoff, convert_unit(300.0, "hartree"))

    def test_section_method_atom_kind(self):
        kind = self.results["section_method_atom_kind"][0]
        self.assertEqual(kind["method_atom_kind_atom_number"], 14)
        self.assertEqual(kind["method_atom_kind_label"], "Si")

    def test_section_method_basis_set(self):
        kind = self.results["section_method_basis_set"][0]
        self.assertEqual(kind["method_basis_set_kind"], "wavefunction")
        self.assertEqual(kind["number_of_basis_sets_atom_centered"], 1)
        self.assertTrue(np.array_equal(kind["mapping_section_method_basis_set_atom_centered"], np.array([[0, 0]])))

    def test_single_configuration_calculation_converged(self):
        result = self.results["single_configuration_calculation_converged"]
        self.assertTrue(result)

    def test_scf_dft_number_of_iterations(self):
        result = self.results["number_of_scf_iterations"]
        self.assertEqual(result, 10)

    def test_single_configuration_to_calculation_method_ref(self):
        result = self.results["single_configuration_to_calculation_method_ref"]
        self.assertEqual(result, 0)

    def test_single_configuration_calculation_to_system_description_ref(self):
        result = self.results["single_configuration_calculation_to_system_ref"]
        self.assertEqual(result, 0)

    def test_stress_tensor(self):
        result = self.results["stress_tensor"]
        expected_result = convert_unit(
            np.array([
                [7.77640934, -0.00000098, -0.00000099],
                [-0.00000098, 7.77640935, -0.00000101],
                [-0.00000099, -0.00000101, 7.77640935],
            ]),
            "GPa"
        )
        self.assertTrue(np.array_equal(result, expected_result))

    def test_stress_tensor_eigenvalues(self):
        result = self.results["x_cp2k_stress_tensor_eigenvalues"]
        expected_result = convert_unit(np.array([7.77640735, 7.77641033, 7.77641036]), "GPa")
        self.assertTrue(np.array_equal(result, expected_result))

    def test_stress_tensor_eigenvectors(self):
        result = self.results["x_cp2k_stress_tensor_eigenvectors"]
        expected_result = np.array([
            [0.57490332, -0.79965737, -0.17330395],
            [0.57753686, 0.54662171, -0.60634634],
            [0.57960102, 0.24850110, 0.77608624],
        ])
        self.assertTrue(np.array_equal(result, expected_result))

    def test_stress_tensor_determinant(self):
        result = self.results["x_cp2k_stress_tensor_determinant"]
        expected_result = convert_unit(4.70259243E+02, "GPa^3")
        self.assertTrue(np.array_equal(result, expected_result))

    def test_stress_tensor_one_third_of_trace(self):
        result = self.results["x_cp2k_stress_tensor_one_third_of_trace"]
        expected_result = convert_unit(7.77640934E+00, "GPa")
        self.assertTrue(np.array_equal(result, expected_result))

    def test_program_basis_set_type(self):
        result = self.results["program_basis_set_type"]
        self.assertEqual(result, "gaussians")


#===============================================================================
class TestPreprocessor(unittest.TestCase):

    def test_include(self):
        result = get_result("input_preprocessing/include", "x_cp2k_input_GLOBAL.PRINT_LEVEL", optimize=False)
        self.assertEqual(result, "LOW")

    def test_variable(self):
        result = get_result("input_preprocessing/variable", "x_cp2k_input_GLOBAL.PROJECT_NAME", optimize=False)
        self.assertEqual(result, "variable_test")

    def test_variable_multiple(self):
        result = get_result("input_preprocessing/variable_multiple", "x_cp2k_input_FORCE_EVAL.DFT.MGRID.CUTOFF", optimize=False)
        self.assertEqual(result, "50")

    def test_comments(self):
        result = get_result("input_preprocessing/comments", "x_cp2k_input_FORCE_EVAL.DFT.MGRID.CUTOFF", optimize=False)
        self.assertEqual(result, "120")

    def test_tabseparator(self):
        result = get_result("input_preprocessing/tabseparator", "x_cp2k_input_FORCE_EVAL.DFT.MGRID.CUTOFF", optimize=False)
        self.assertEqual(result, "120")


#===============================================================================
class TestGeoOpt(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.results = get_results("geo_opt/cg", "section_run")

    def test_geometry_optimization_converged(self):
        result = self.results["geometry_optimization_converged"]
        self.assertTrue(result)

    def test_number_of_frames_in_sequence(self):
        result = self.results["number_of_frames_in_sequence"]
        self.assertEqual(result, 7)

    def test_frame_sequence_to_sampling_ref(self):
        result = self.results["frame_sequence_to_sampling_ref"]
        self.assertEqual(result, 0)

    def test_frame_sequence_local_frames_ref(self):
        result = self.results["frame_sequence_local_frames_ref"]
        expected_result = np.array([0, 1, 2, 3, 4, 5, 6])
        self.assertTrue(np.array_equal(result, expected_result))

    def test_sampling_method(self):
        result = self.results["sampling_method"]
        self.assertEqual(result, "geometry_optimization")

    def test_geometry_optimization_method(self):
        result = self.results["geometry_optimization_method"]
        self.assertEqual(result, "conjugate_gradient")

    def test_geometry_optimization_geometry_change(self):
        result = self.results["geometry_optimization_geometry_change"]
        expected_result = convert_unit(
            0.0010000000,
            "bohr"
        )
        self.assertEqual(result, expected_result)

    def test_geometry_optimization_threshold_force(self):
        result = self.results["geometry_optimization_threshold_force"]
        expected_result = convert_unit(
            0.0010000000,
            "bohr^-1*hartree"
        )
        self.assertEqual(result, expected_result)

    def test_frame_sequence_potential_energy(self):
        result = self.results["frame_sequence_potential_energy"]
        expected_result = convert_unit(
            np.array([
                -17.1534159246,
                -17.1941015290,
                -17.2092321965,
                -17.2097667733,
                -17.2097743028,
                -17.2097743229,
                -17.20977820662248,
            ]),
            "hartree"
        )
        self.assertTrue(np.array_equal(result, expected_result))

    def test_atom_positions(self):
        result = self.results["atom_positions"]
        expected_start = convert_unit(
            np.array([
                [12.2353220000, 1.3766420000, 10.8698800000],
                [12.4175775999, 2.2362362573, 11.2616216864],
                [11.9271436933, 1.5723516602, 10.0115134757],
            ]),
            "angstrom"
        )

        expected_end = convert_unit(
            np.array([
                [12.2353220000, 1.3766420000, 10.8698800000],
                [12.4958164689, 2.2307248873, 11.3354322515],
                [11.9975558616, 1.5748085240, 10.0062792262],
            ]),
            "angstrom"
        )
        result_start = result[0, :, :]
        result_end = result[-1, :, :]
        self.assertTrue(np.array_equal(result_start, expected_start))
        self.assertTrue(np.array_equal(result_end, expected_end))


# ===============================================================================
class TestGeoOptTrajFormats(unittest.TestCase):

    def test_xyz(self):

        result = get_result("geo_opt/geometry_formats/xyz", "atom_positions", optimize=True)
        expected_start = convert_unit(
            np.array([
                [12.2353220000, 1.3766420000, 10.8698800000],
                [12.4175624065, 2.2362390825, 11.2616392180],
                [11.9271777126, 1.5723402996, 10.0115089094],
            ]),
            "angstrom"
        )
        expected_end = convert_unit(
            np.array([
                [12.2353220000, 1.3766420000, 10.8698800000],
                [12.4957995882, 2.2307218433, 11.3354453867],
                [11.9975764125, 1.5747996320, 10.0062529540],
            ]),
            "angstrom"
        )
        result_start = result[0, :, :]
        result_end = result[-1, :, :]
        self.assertTrue(np.array_equal(result_start, expected_start))
        self.assertTrue(np.array_equal(result_end, expected_end))

    def test_pdb(self):
        result = get_result("geo_opt/geometry_formats/pdb", "atom_positions", optimize=True)
        expected_start = convert_unit(
            np.array([
                [12.235, 1.377, 10.870],
                [12.418, 2.236, 11.262],
                [11.927, 1.572, 10.012],
            ]),
            "angstrom"
        )
        expected_end = convert_unit(
            np.array([
                [12.235, 1.377, 10.870],
                [12.496, 2.231, 11.335],
                [11.998, 1.575, 10.006],
            ]),
            "angstrom"
        )
        result_start = result[0, :, :]
        result_end = result[-1, :, :]
        self.assertTrue(np.array_equal(result_start, expected_start))
        self.assertTrue(np.array_equal(result_end, expected_end))

    def test_dcd(self):
        result = get_result("geo_opt/geometry_formats/dcd", "atom_positions", optimize=True)
        frames = result.shape[0]
        self.assertEqual(frames, 7)


#===============================================================================
class TestGeoOptOptimizers(unittest.TestCase):

    def test_bfgs(self):
        result = get_result("geo_opt/bfgs", "geometry_optimization_method")
        self.assertEqual(result, "bfgs")

    def test_lbfgs(self):
        result = get_result("geo_opt/lbfgs", "geometry_optimization_method")
        self.assertEqual(result, "bfgs")


#===============================================================================
class TestGeoOptTrajectory(unittest.TestCase):

    def test_each_and_add_last(self):
        """Test that the EACH and ADD_LAST settings affect the parsing
        correctly.
        """
        results = get_results("geo_opt/each")

        single_conf = results["section_single_configuration_calculation"]
        systems = results["section_system"]

        i_conf = 0
        for calc in single_conf:
            system_index = calc["single_configuration_calculation_to_system_ref"]
            system = systems[system_index]

            if i_conf == 0 or i_conf == 2 or i_conf == 4:
                with self.assertRaises(ParserKeyError):
                    pos = system["atom_positions"]
            else:
                pos = system["atom_positions"]
                if i_conf == 1:
                    expected_pos = convert_unit(
                        np.array([
                            [12.2353220000, 1.3766420000, 10.8698800000],
                            [12.4618486015, 2.2314871691, 11.3335607388],
                            [11.9990227122, 1.5776813026, 10.0384213366],
                        ]),
                        "angstrom"
                    )
                    self.assertTrue(np.array_equal(pos, expected_pos))
                if i_conf == 3:
                    expected_pos = convert_unit(
                        np.array([
                            [12.2353220000, 1.3766420000, 10.8698800000],
                            [12.4962705528, 2.2308411983, 11.3355758433],
                            [11.9975151486, 1.5746309898, 10.0054430868],
                        ]),
                        "angstrom"
                    )
                    self.assertTrue(np.array_equal(pos, expected_pos))
                if i_conf == 5:
                    expected_pos = convert_unit(
                        np.array([
                            [12.2353220000, 1.3766420000, 10.8698800000],
                            [12.4958168364, 2.2307249171, 11.3354322532],
                            [11.9975556812, 1.5748088251, 10.0062793864],
                        ]),
                        "angstrom"
                    )
                    self.assertTrue(np.array_equal(pos, expected_pos))

                if i_conf == 6:
                    expected_pos = convert_unit(
                        np.array([
                            [12.2353220000, 1.3766420000, 10.8698800000],
                            [12.4958164689, 2.2307248873, 11.3354322515],
                            [11.9975558616, 1.5748085240, 10.0062792262],
                        ]),
                        "angstrom"
                    )
                    self.assertTrue(np.array_equal(pos, expected_pos))

            i_conf += 1


#===============================================================================
class TestMD(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.results = get_results("md/nve", "section_run")
        cls.temp = convert_unit(
            np.array([
                300.000000000,
                275.075405378,
                235.091633019,
                202.752506973,
                192.266488819,
                201.629598676,
                218.299664775,
                230.324748557,
                232.691881533,
                226.146979313,
                213.165337396,
            ]),
            "K"
        )
        cls.cons = convert_unit(
            np.array([
                -34.323271136,
                -34.323245645,
                -34.323206964,
                -34.323183380,
                -34.323187747,
                -34.323208962,
                -34.323227533,
                -34.323233583,
                -34.323230715,
                -34.323227013,
                -34.323224123,
            ]),
            "hartree"
        )
        cls.pot = convert_unit(
            np.array([
                -34.330396471,
                -34.329778993,
                -34.328790653,
                -34.327998978,
                -34.327754290,
                -34.327997890,
                -34.328412394,
                -34.328704052,
                -34.328757407,
                -34.328598255,
                -34.328287038,
            ]),
            "hartree"
        )
        cls.kin = convert_unit(
            np.array([
                0.007125335,
                0.006533348,
                0.005583688,
                0.004815598,
                0.004566544,
                0.004788928,
                0.005184860,
                0.005470470,
                0.005526692,
                0.005371243,
                0.005062914,
            ]),
            "hartree"
        )

    def test_number_of_atoms(self):
        result = self.results["number_of_atoms"]
        expected_result = np.array(11*[6])
        self.assertTrue(np.array_equal(result, expected_result))

    def test_simulation_cell(self):
        result = self.results["simulation_cell"]
        self.assertEqual(len(result), 11)
        expected_start = convert_unit(
            np.array([
                [9.853, 0, 0],
                [0, 9.853, 0],
                [0, 0, 9.853],
            ]),
            "angstrom"
        )
        self.assertTrue(np.array_equal(result[0], expected_start))

    def test_ensemble_type(self):
        result = self.results["ensemble_type"]
        self.assertEqual(result, "NVE")

    def test_sampling_method(self):
        result = self.results["sampling_method"]
        self.assertEqual(result, "molecular_dynamics")

    def test_number_of_frames_in_sequence(self):
        result = self.results["number_of_frames_in_sequence"]
        self.assertEqual(result, 11)

    def test_atom_positions(self):
        result = self.results["atom_positions"]
        expected_start = convert_unit(
            np.array([
                [2.2803980000, 9.1465390000, 5.0886960000],
                [1.2517030000, 2.4062610000, 7.7699080000],
                [1.7620190000, 9.8204290000, 5.5284540000],
                [3.0959870000, 9.1070880000, 5.5881860000],
                [0.5541290000, 2.9826340000, 8.0820240000],
                [1.7712570000, 2.9547790000, 7.1821810000],
            ]),
            "angstrom"
        )
        expected_end = convert_unit(
            np.array([
                [2.2916014875, 9.1431763260, 5.0868100688],
                [1.2366834078, 2.4077552776, 7.7630044423],
                [1.6909790671, 9.8235337924, 5.5042564094],
                [3.1130341664, 9.0372111810, 5.6100739746],
                [0.5652070478, 3.0441761067, 8.1734257299],
                [1.8669280879, 2.9877213524, 7.2364955946],
            ]),
            "angstrom"
        )
        self.assertTrue(np.array_equal(result[0, :], expected_start))
        self.assertTrue(np.array_equal(result[-1, :], expected_end))

    def test_atom_velocities(self):
        result = self.results["atom_velocities"]
        expected_start = convert_unit(
            np.array([
                [0.0000299284, 0.0000082360, -0.0000216368],
                [-0.0001665963, 0.0001143863, -0.0000622640],
                [-0.0005732926, -0.0003112611, -0.0007149779],
                [0.0013083605, -0.0009262219, 0.0006258560],
                [0.0012002313, -0.0003701042, 0.0002810523],
                [0.0002340810, -0.0003388418, 0.0011398583],
            ]),
            "bohr*(hbar/hartree)^-1"
        )
        expected_end = convert_unit(
            np.array([
                [0.0001600263, -0.0000383308, 0.0000153662],
                [-0.0001269381, -0.0000005151, -0.0000726214],
                [0.0000177093, -0.0003257814, -0.0000257852],
                [-0.0015067045, -0.0001700489, -0.0003651605],
                [0.0000307926, 0.0006886719, 0.0008431321],
                [0.0007424681, 0.0003614127, 0.0005749089],
            ]),
            "bohr*(hbar/hartree)^-1"
        )

        self.assertTrue(np.array_equal(result[0, :], expected_start))
        self.assertTrue(np.array_equal(result[-1, :], expected_end))

    def test_frame_sequence_potential_energy(self):
        result = self.results["frame_sequence_potential_energy"]
        self.assertTrue(np.array_equal(result, self.pot))

    def test_frame_sequence_kinetic_energy(self):
        result = self.results["frame_sequence_kinetic_energy"]
        self.assertTrue(np.array_equal(result, self.kin))

    def test_frame_sequence_conserved_quantity(self):
        result = self.results["frame_sequence_conserved_quantity"]
        self.assertTrue(np.array_equal(result, self.cons))

    def test_frame_sequence_temperature(self):
        result = self.results["frame_sequence_temperature"]
        self.assertTrue(np.array_equal(result, self.temp))

    def test_frame_sequence_time(self):
        result = self.results["frame_sequence_time"]
        expected_result = convert_unit(
            np.array([
                0.000000,
                0.500000,
                1.000000,
                1.500000,
                2.000000,
                2.500000,
                3.000000,
                3.500000,
                4.000000,
                4.500000,
                5.000000,
            ]),
            "fs"
        )
        self.assertTrue(np.array_equal(result, expected_result))

    def test_frame_sequence_potential_energy_stats(self):
        result = self.results["frame_sequence_potential_energy_stats"]
        expected_result = np.array([self.pot.mean(), self.pot.std()])
        self.assertTrue(np.array_equal(result, expected_result))

    def test_frame_sequence_kinetic_energy_stats(self):
        result = self.results["frame_sequence_kinetic_energy_stats"]
        expected_result = np.array([self.kin.mean(), self.kin.std()])
        self.assertTrue(np.array_equal(result, expected_result))

    def test_frame_sequence_conserved_quantity_stats(self):
        result = self.results["frame_sequence_conserved_quantity_stats"]
        expected_result = np.array([self.cons.mean(), self.cons.std()])
        self.assertTrue(np.array_equal(result, expected_result))

    def test_frame_sequence_temperature_stats(self):
        result = self.results["frame_sequence_temperature_stats"]
        expected_result = np.array([self.temp.mean(), self.temp.std()])
        self.assertTrue(np.array_equal(result, expected_result))


#===============================================================================
class TestMDEnsembles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pressure = convert_unit(
            np.array([
                -0.192828092559E+04,
                -0.145371071470E+04,
                -0.210098903760E+03,
                0.167260570313E+04,
                0.395562042841E+04,
                0.630374855942E+04,
                0.836906136786E+04,
                0.983216022830E+04,
                0.104711540465E+05,
                0.102444821550E+05,
                0.931695792434E+04,
            ]),
            "bar"
        )

    def test_nvt(self):
        results = get_results("md/nvt", "section_run")
        ensemble = results["ensemble_type"]
        self.assertEqual(ensemble, "NVT")

    def test_npt(self):
        results = get_results("md/npt", "section_run")
        ensemble = results["ensemble_type"]
        self.assertEqual(ensemble, "NPT")

        pressure = results["frame_sequence_pressure"]
        self.assertTrue(np.array_equal(pressure, self.pressure))

        pressure_stats = results["frame_sequence_pressure_stats"]
        expected_pressure_stats = np.array([self.pressure.mean(), self.pressure.std()])
        self.assertTrue(np.array_equal(pressure_stats, expected_pressure_stats))

        simulation_cell = results["simulation_cell"]
        expected_cell_start = convert_unit(
            np.array(
                [[
                    6.0000000000,
                    0.0000000000,
                    0.0000000000,
                ], [
                    0.0000000000,
                    6.0000000000,
                    0.0000000000,
                ], [
                    0.0000000000,
                    0.0000000000,
                    6.0000000000,
                ]]),
            "angstrom"
        )
        expected_cell_end = convert_unit(
            np.array(
                [[
                    5.9960617905,
                    -0.0068118798,
                    -0.0102043036,
                ], [
                    -0.0068116027,
                    6.0225574669,
                    -0.0155044063,
                ], [
                    -0.0102048226,
                    -0.0155046726,
                    6.0083072343,
                ]]),
            "angstrom"
        )
        self.assertEqual(simulation_cell.shape[0], 11)
        self.assertTrue(np.array_equal(expected_cell_start, simulation_cell[0, :, :]))
        self.assertTrue(np.array_equal(expected_cell_end, simulation_cell[-1, :, :]))


#===============================================================================
class TestElectronicStructureMethod(unittest.TestCase):

    def test_mp2(self):
        results = get_results("electronic_structure_method/mp2", "section_run")
        result = results["electronic_structure_method"]
        self.assertEqual(result, "MP2")

    def test_dft_plus_u(self):
        results = get_results("electronic_structure_method/dft_plus_u", "section_run")
        result = results["electronic_structure_method"]
        self.assertEqual(result, "DFT+U")

    def test_rpa(self):
        results = get_results("electronic_structure_method/rpa", "section_run")
        result = results["electronic_structure_method"]
        self.assertEqual(result, "RPA")


#===============================================================================
if __name__ == '__main__':
    logger = logging.getLogger("cp2kparser")
    logger.setLevel(logging.ERROR)

    suites = []
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestErrors))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestXCFunctional))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestEnergyForce))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestStressTensorMethods))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestSelfInteractionCorrectionMethod))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestConfigurationPeriodicDimensions))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestSCFConvergence))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestForceFiles))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestPreprocessor))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestGeoOpt))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestGeoOptTrajFormats))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestGeoOptOptimizers))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestGeoOptTrajectory))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestMD))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestMDEnsembles))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestElectronicStructureMethod))
    alltests = unittest.TestSuite(suites)
    unittest.TextTestRunner(verbosity=0).run(alltests)
