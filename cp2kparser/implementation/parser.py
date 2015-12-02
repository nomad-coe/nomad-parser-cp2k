import os
import re
from cp2kparser.generics.nomadparser import NomadParser, Result, ResultCode
from cp2kparser.implementation.regexs import *
from cp2kparser.engines.regexengine import RegexEngine
from cp2kparser.engines.csvengine import CSVEngine
from cp2kparser.engines.cp2kinputengine import CP2KInputEngine
from cp2kparser.engines.xmlengine import XMLEngine
from cp2kparser.engines.atomsengine import AtomsEngine
import numpy as np
import logging
import sys
logger = logging.getLogger(__name__)
from cp2kparser import ureg


#===============================================================================
class CP2KParser(NomadParser):
    """The interface for a NoMaD CP2K parser. All parsing actions will go
    through this class.

    The CP2K version 2.6.2 was used as a reference for this basic
    implementation. For other versions there should be classes that extend from
    this.
    """
    def __init__(self, input_json_string, stream=sys.stdout, test_mode=False):

        # Initialize the base class
        NomadParser.__init__(self, input_json_string, stream, test_mode)

        # Engines are created here
        self.csvengine = CSVEngine(self)
        self.regexengine = RegexEngine(self)
        self.xmlengine = XMLEngine(self)
        self.inputengine = CP2KInputEngine()
        self.atomsengine = AtomsEngine()

        self.version_number = None
        self.implementation = None
        self.input_tree = None
        self.regexs = None

        # Use some convenient functions from base
        self.determine_file_ids_pre_setup()
        self.setup_version()
        self.determine_file_ids_post_setup()

    def get_supported_quantities(self):
        """Inherited from NomadParser.
        """
        supported_quantities = []
        implementation_methods = [method for method in dir(self.implementation) if callable(getattr(self.implementation, method))]
        for method in implementation_methods:
            if method.startswith("_Q_"):
                method = method[3:]
                supported_quantities.append(method)

        return supported_quantities

    def setup_version(self):
        """Inherited from NomadParser.
        """
        # Determine the CP2K version from the output file
        beginning = self.read_part_of_file("output", 2048)
        version_regex = re.compile(r"CP2K\|\ version\ string:\s+CP2K\ version\ (\d+\.\d+\.\d+)\n")
        self.version_number = version_regex.search(beginning).groups()[0].replace('.', '')
        self.inputengine.setup_version_number(self.version_number)
        self.input_tree = self.inputengine.parse(self.get_file_contents("input"))
        version_name = '_' + self.version_number + '_'

        # Search for a version specific regex class
        class_name = "CP2K{}Regexs".format(version_name)
        self.regexs = globals().get(class_name)
        if self.regexs:
            logger.debug("Using version specific regexs '{}'.".format(class_name))
            self.regexs = self.regexs()
        else:
            logger.debug("Using default regexs.")
            self.regexs = globals()["CP2KRegexs"]()

        # Search for a version specific implementation
        class_name = "CP2K{}Implementation".format(version_name)
        class_object = globals().get(class_name)
        if class_object:
            logger.debug("Using version specific implementation '{}'.".format(class_name))
            self.implementation = class_object(self)
        else:
            logger.debug("Using default implementation.")
            self.implementation = globals()["CP2KImplementation"](self)

    def start_parsing(self, name):
        """Inherited from NomadParser.
        """
        # Ask the implementation for the quantity
        function = getattr(self.implementation, "_Q_" + name)
        if function:
            return function()
        else:
            logger.error("The function for quantity '{}' is not defined".format(name))

    def read_part_of_file(self, file_id, size=1024):
        fh = self.get_file_handle(file_id)
        buffer = fh.read(size)
        return buffer

    def determine_file_ids_pre_setup(self):
        """First resolve the files that can be identified by extension.
        """
        for file_path in self.files.iterkeys():
            if file_path.endswith(".inp"):
                self.setup_file_id(file_path, "input")
            if file_path.endswith(".out"):
                self.setup_file_id(file_path, "output")

    def determine_file_ids_post_setup(self):
        """Inherited from NomadParser.
        """
        # Determine the presence of force file
        force_path = self.input_tree.get_keyword("FORCE_EVAL/PRINT/FORCES/FILENAME")
        project_name = self.input_tree.get_keyword("GLOBAL/PROJECT_NAME")
        if force_path is not None and force_path != "__STD_OUT__":

            # The force path is not typically exactly as written in input
            if force_path.startswith("="):
                logger.debug("Using single force file.")
                force_path = force_path[1:]
            elif re.match(r".?/", force_path):
                logger.debug("Using separate force file for each step.")
                force_path = "{}-1_0.xyz".format(force_path)
            else:
                logger.debug("Using separate force file for each step.")
                force_path = "{}-{}-1_0.xyz".format(project_name, force_path)
            force_path = os.path.basename(force_path)

            # Check against the given files
            file_path = self.search_file(force_path)
            self.file_ids["forces"] = file_path
            self.get_file_handle("forces")

        # Determine the presence of an initial coordinate file
        init_coord_file = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_NAME")
        if init_coord_file is not None:
            logger.debug("Initial coordinate file found.")
            # Check against the given files
            file_path = self.search_file(init_coord_file)
            self.file_ids["initial_coordinates"] = file_path
            self.get_file_handle("initial_coordinates")

        # Determine the presence of a trajectory file
        traj_file = self.input_tree.get_keyword("MOTION/PRINT/TRAJECTORY/FILENAME")
        if traj_file is not None:
            logger.debug("Trajectory file found.")
            normalized_path = self.normalize_cp2k_traj_path(traj_file)
            file_path = self.search_file(normalized_path)
            self.file_ids["trajectory"] = file_path
            self.get_file_handle("trajectory")

    def normalize_cp2k_traj_path(self, path):
        logger.debug("Normalizing trajectory path")
        project_name = self.input_tree.get_keyword("GLOBAL/PROJECT_NAME")
        file_format = self.input_tree.get_keyword("MOTION/PRINT/TRAJECTORY/FORMAT")
        extension = {
            "PDB": "pdb",
            "XYZ": "xyz",
            "XMOL": "xyz",
            "ATOMIC": "xyz",
            "DCD": "dcd",
        }[file_format]
        if path.startswith("="):
            normalized_path = path[1:]
        elif re.match(r"./", path):
            normalized_path = "{}-pos-1.{}".format(path, extension)
        else:
            normalized_path = "{}-{}-pos-1.{}".format(project_name, path, extension)
        return normalized_path

    def search_file(self, path):
        """Searches the list of given files for a file that is defined in the
        CP2K input file.

        First compares the basenames, and if multiple matches found descends
        the path until only one or zero matches found.
        """
        matches = {}
        resolvable = [x for x in self.files.iterkeys() if x not in self.file_ids.itervalues()]

        for file_path in resolvable:
            available_parts = self.split_path(file_path)
            searched_parts = self.split_path(path)
            for i_part, part in enumerate(searched_parts):
                if part == available_parts[i_part]:
                    matches[file_path] = i_part

        n = len(matches)
        if n == 1:
            return matches.keys()[0]
        elif n == 0:
            logger.error("Could not find file '{}' specified in CP2K input.".format(path))
            return
        else:
            sorted_list = [(k, v) in sorted(mydict.items(), key=lambda (k, v): v[1])]
            # sorted_list = sorted(mathes, key=lambda k: matches[k])
            if (sorted_list[0][1] == sorted_list[1][1]):
                logger.error("When searching for file '{}', multiple matches were found. Could not determine which file to use based on their path.")
            else:
                return sorted_list[0][0]

    def split_path(self, path):
        folders = []
        while 1:
            path, folder = os.path.split(path)

            if folder != "":
                folders.append(folder)
            else:
                if path != "":
                    folders.append(path)

                break

        return folders

    def get_all_quantities(self):
        """Parse all supported quantities."""
        for method in self.get_supported_quantities:
            self.get_quantity(method)


#===============================================================================
class CP2KImplementation(object):
    """Defines the basic functions that are used to map results to the
    corresponding NoMaD quantities.

    This class provides the basic implementations and for a version specific
    updates and additions please make a new class that inherits from this.

    The functions that return certain quantities are tagged with a prefix '_Q_'
    to be able to automatically determine which quantities have at least some
    level of support. With the tag they can be also looped through.
    """
    def __init__(self, parser):
        self.parser = parser
        self.regexs = parser.regexs
        self.regexengine = parser.regexengine
        self.csvengine = parser.csvengine
        self.atomsengine = parser.atomsengine
        self.input_tree = parser.input_tree

    def decode_cp2k_unit(self, unit):
        """Given a CP2K unit name, decode it as Pint unit definition.
        """
        map = {
            # Length
            "bohr": ureg.bohr,
            "m": ureg.meter,
            "pm": ureg.picometer,
            "nm": ureg.nanometer,
            "angstrom": ureg.angstrom,
        }

        pint_unit = map.get(unit)
        if pint_unit:
            return pint_unit
        else:
            logger.error("Unknown CP2K unit definition given.")

    def _Q_energy_total(self):
        """Return the total energy from the bottom of the input file"""
        result = Result()
        result.unit = ureg.hartree
        result.value = float(self.regexengine.parse(self.regexs.energy_total, self.parser.get_file_handle("output")))
        return result

    def _Q_XC_functional(self):
        """Returns the type of the XC functional.

        Can currently only determine version if they are declared as parameters
        for XC_FUNCTIONAL or via activating subsections of XC_FUNCTIONAL.

        Returns:
            A string containing the final result that should
            belong to the list defined in NoMaD wiki.
        """
        result = Result()

        # First try to look at the shortcut
        xc_shortcut = self.input_tree.get_parameter("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL")
        if xc_shortcut is not None and xc_shortcut != "NONE" and xc_shortcut != "NO_SHORTCUT":
            logger.debug("Shortcut defined for XC_FUNCTIONAL")

            # If PBE, check version
            if xc_shortcut == "PBE":
                pbe_version = self.input_tree.get_keyword("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/PBE/PARAMETRIZATION")
                result.value = {
                        'ORIG': "GGA_X_PBE",
                        'PBESOL': "GGA_X_PBE_SOL",
                        'REVPBE': "GGA_X_PBE_R",
                }.get(pbe_version, "GGA_X_PBE")
                return result

            result.value = {
                    'B3LYP': "HYB_GGA_XC_B3LYP",
                    'BEEFVDW': None,
                    'BLYP': "GGA_C_LYP_GGA_X_B88",
                    'BP': None,
                    'HCTH120': None,
                    'OLYP': None,
                    'LDA': "LDA_XC_TETER93",
                    'PADE': "LDA_XC_TETER93",
                    'PBE0': None,
                    'TPSS': None,
            }.get(xc_shortcut, None)
            return result
        else:
            logger.debug("No shortcut defined for XC_FUNCTIONAL. Looking into subsections.")

        # Look at the subsections and determine what part have been activated

        # Becke88
        xc_components = []
        becke_88 = self.input_tree.get_parameter("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE88")
        if becke_88 == "TRUE":
            xc_components.append("GGA_X_B88")

        # Becke 97
        becke_97 = self.input_tree.get_parameter("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE97")
        if becke_97 == "TRUE":
            becke_97_param = self.input_tree.get_keyword("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE97/PARAMETRIZATION")
            becke_97_result = {
                    'B97GRIMME': None,
                    'B97_GRIMME': None,
                    'ORIG': "GGA_XC_B97",
                    'WB97X-V': None,
            }.get(becke_97_param, None)
            if becke_97_result is not None:
                xc_components.append(becke_97_result)

        # Return an alphabetically sorted and joined list of the xc components
        result.value = "_".join(sorted(xc_components))
        return result

    def _Q_particle_forces(self):
        """Return the forces that are controlled by
        "FORCE_EVAL/PRINT/FORCES/FILENAME". These forces are typicalle printed
        out during optimization or single point calculation.

        Supports forces printed in the output file or in a single XYZ file.
        """
        result = Result()
        result.unit = ureg.force_au

        # Determine if a separate force file is used or are the forces printed
        # in the output file.
        separate_file = True
        filename = self.input_tree.get_keyword("FORCE_EVAL/PRINT/FORCES/FILENAME")
        if not filename or filename == "__STD_OUT__":
            separate_file = False

        # Look for the forces either in output or in separate file
        if not separate_file:
            logger.debug("Looking for forces in output file.")
            forces = self.regexengine.parse(self.regexs.particle_forces, self.parser.get_file_handle("output"))
            if forces is None:
                msg = "No force configurations were found when searching the output file."
                logger.warning(msg)
                result.error_message = msg
                result.code = ResultCode.fail
                return result

            # Insert force configuration into the array
            i_conf = 0
            force_array = None
            for force_conf in forces:
                iterator = self.csvengine.iread(force_conf, columns=(-3, -2, -1), comments=("#", "ATOMIC", "SUM"), separator=None)
                i_force_array = iterator.next()

                # Initialize the numpy array if not done yet
                n_particles = i_force_array.shape[0]
                n_dim = i_force_array.shape[1]
                n_confs = len(forces)
                force_array = np.empty((n_confs, n_particles, n_dim))

                force_array[i_conf, :, :] = i_force_array
                i_conf += 1

            result.value_iterable = force_array
            return result
        else:
            logger.debug("Looking for forces in separate force file.")
            iterator = self.csvengine.iread(self.parser.get_file_handle("forces"), columns=(-3, -2, -1), comments=("#", "SUM"), separator=r"\ ATOMIC FORCES in \[a\.u\.\]")
            result.value_iterable = iterator
            return result

    def _Q_particle_number(self):
        """Return the number of particles in the system.

        CP2K output doesn't automatically print the number of atoms. For this
        reason this function has to look at the initial configuration and
        calculate the number from it. The initial configuration is something
        that must be present for all calculations.
        """
        result = Result()
        result.cache = True

        # Check where the coordinates are specified
        coord_format = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_FORMAT")
        if not coord_format:
            coord_format = self.input_tree.get_keyword_default("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_FORMAT")

        # Check if the unit cell is multiplied programmatically
        multiples = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/MULTIPLE_UNIT_CELL")
        if not multiples:
            multiples = self.input_tree.get_keyword_default("FORCE_EVAL/SUBSYS/TOPOLOGY/MULTIPLE_UNIT_CELL")
        factors = [int(x) for x in multiples.split()]
        factor = np.prod(np.array(factors))

        # See if the coordinates are provided in the input file
        if coord_format == "OFF":
            logger.debug("Using coordinates from the input file.")
            coords = self.input_tree.get_default_keyword("FORCE_EVAL/SUBSYS/COORD")
            coords.strip()
            n_particles = coords.count("\n")
            result.value = factor*n_particles
        elif coord_format in ["CP2K", "G96", "XTL", "CRD"]:
            msg = "Tried to read the number of atoms from the initial configuration, but the parser does not yet support the '{}' format that is used by file '{}'.".format(coord_format, self.parser.file_ids["initial_coordinates"])
            logger.warning(msg)
            result.error_message = msg
            result.code = ResultCode.fail
        else:
            # External file, use AtomsEngine
            init_coord_file = self.parser.get_file_handle("initial_coordinates")
            if coord_format == "XYZ":
                n_particles = self.atomsengine.n_atoms(init_coord_file, format="xyz")
            if coord_format == "CIF":
                n_particles = self.atomsengine.n_atoms(init_coord_file, format="cif")
            if coord_format == "PDB":
                n_particles = self.atomsengine.n_atoms(init_coord_file, format="pdb")

        result.value = factor*n_particles
        return result

    def _Q_particle_position(self):
        """Returns the particle positions (trajectory).
        """
        result = Result()

        # Determine the unit
        unit = self.input_tree.get_keyword("MOTION/PRINT/TRAJECTORY/UNIT")
        unit = unit.lower()
        result.unit = self.decode_cp2k_unit(unit)

        # Read the trajectory
        traj_file = self.parser.get_file_handle("trajectory")
        input_file_format = self.input_tree.get_keyword("MOTION/PRINT/TRAJECTORY/FORMAT")
        file_format = {
            "XYZ": "xyz",
            "XMOL": "xyz",
            "PDB": "pdb-cp2k",
            "ATOMIC": "atomic",
        }.get(input_file_format)

        if file_format is None:
            logger.error("Unsupported trajectory file format '{}'.".format(input_file_format))

        # Use a custom implementation for the CP2K specific weird formats
        if file_format == "pdb-cp2k":
            traj_iter = self.parser.csvengine.iread(traj_file, columns=[3, 4, 5], comments=["TITLE", "AUTHOR", "REMARK", "CRYST"], separator="END")
        elif file_format == "atomic":
            n_atoms = self.parser.get_result_object("particle_number").value

            def atomic_generator():
                conf = []
                i = 0
                for line in traj_file:
                    line = line.strip()
                    components = np.array([float(x) for x in line.split()])
                    conf.append(components)
                    i += 1
                    if i == n_atoms:
                        yield np.array(conf)
                        conf = []
                        i = 0
            traj_iter = atomic_generator()
        else:
            traj_iter = self.atomsengine.iread(traj_file, format=file_format)

        # Return the iterator
        result.value_iterable = traj_iter
        return result

    def _Q_cell(self):

        # Cell given as three vectors
        A = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/A")
        B = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/B")
        C = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/C")

        if A and B and C:
            return

        # Cell given as three lengths and three angles
        ABC = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/ABC")
        abg = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/ALPHA_BETA_GAMMA")

        # Cell given in external file
        cell_format = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/CELL_FILE_FORMAT")
        cell_file = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/CELL_FILE_NAME")

        # Multiplication factor
        factor = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/CELL_FILE_NAME")


#===============================================================================
class CP2K_262_Implementation(CP2KImplementation):
    def __init__(self, parser):
        CP2KImplementation.__init__(self, parser)
