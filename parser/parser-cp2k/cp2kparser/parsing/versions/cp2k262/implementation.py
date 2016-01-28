import re
import os
import logging
from cp2kparser.parsing.csvparsing import CSVParser
from .inputparsing import CP2KInputParser
from .outputparser import CP2KOutputParser
from cp2kparser.parsing.cp2kinputenginedata.input_tree import CP2KInput
from cp2kparser.utils.baseclasses import ParserImplementation
from nomadcore.coordinate_reader import CoordinateReader
logger = logging.getLogger(__name__)


#===============================================================================
class CP2KImplementation(ParserImplementation):
    """The default implementation for a CP2K parser based on version 2.6.2.
    """
    def __init__(self, parser_context):

        # Initialize the base class
        ParserImplementation.__init__(self, parser_context)

        # Initialize the parsing tools. The input and output parsers need to
        # know the version id.
        self.csvengine = CSVParser(self)
        self.atomsengine = CoordinateReader()
        self.inputparser = CP2KInputParser()
        self.inputparser.setup_version(self.version_id)
        self.input_tree = None
        self.extended_input = None

        self.determine_file_ids_pre_setup()
        self.input_preprocessor()
        self.determine_file_ids_post_setup()

    def determine_file_ids_pre_setup(self):
        """Resolve the input and output files based on extension and the
        include files by looking for @INCLUDE commands in the input file.
        """

        # Input and output files
        for file_path in self.files:
            if file_path.endswith(".inp"):
                self.setup_file_id(file_path, "input")
            if file_path.endswith(".out"):
                self.setup_file_id(file_path, "output")
                outputparser = CP2KOutputParser(file_path, self.parser_context)
                self.file_parsers.append(outputparser)

        # Include files
        input_file = self.get_file_contents("input")
        for line in input_file.split("\n"):
            line = line.strip()
            if line.startswith("@INCLUDE") or line.startswith("@include"):
                split = line.split(None, 1)
                filename = split[1]
                if filename.startswith(('\"', '\'')) and filename.endswith(('\"', '\'')):
                    filename = filename[1:-1]
                filepath = self.search_file(filename)
                self.setup_file_id(filepath, "include")

    # def determine_output_file(self):
        # """Determine which of the given files is the output file.
        # """
        # # If a main file has been specified it is the output file.
        # if self.parser_context.main_file is not None:
            # self.setup_file_id(file_path, "output")
        # # Otherwise try to determine by the file extension
        # else:
            # n_outfiles = 0
            # for file_path in self.files:
                # if file_path.endswith(".out"):
                    # n_outfiles += 1
                    # self.setup_file_id(file_path, "output")
                    # self.outputparser = globals()["CP2KOutputParser{}".format(self.version_id)](file_path, self.parser_context)
                    # self.file_parsers.append(self.outputparser)

    def input_preprocessor(self):
        """Preprocess the input file. Concatenate .inc files into the main
        input file and explicitly state all variables.
        """
        # Merge include files to input
        include_files = self.get_file_handles("include", show_warning=False)
        input_file = self.get_file_contents("input")
        input_lines = input_file.split("\n")
        extended_input = input_lines[:]  # Make a copy
        if include_files:
            i_line = 0
            for line in input_lines:
                line = line.strip()
                if line.startswith("@INCLUDE") or line.startswith("@include"):
                    split = line.split(None, 1)
                    filename = split[1]
                    if filename.startswith(('\"', '\'')) and filename.endswith(('\"', '\'')):
                        filename = filename[1:-1]
                    filepath = self.search_file(filename)

                    # Get the content from include file
                    for handle in include_files:
                        name = handle.name
                        if name == filepath:
                            contents = handle.read()
                            contents = contents.split('\n')
                            del extended_input[i_line]
                            extended_input[i_line:i_line] = contents
                            i_line += len(contents)
                i_line += 1

        # Gather the variable definitions
        variables = {}
        input_set_removed = []
        for i_line, line in enumerate(extended_input):
            if line.startswith("@SET") or line.startswith("@set"):
                components = line.split(None, 2)
                name = components[1]
                value = components[2]
                variables[name] = value
                logger.debug("Variable '{}' found with value '{}'".format(name, value))
            else:
                input_set_removed.append(line)

        # Place the variables
        variable_pattern = r"\@\{(\w+)\}|@(\w+)"
        compiled = re.compile(variable_pattern)
        reserved = ("include", "set", "if", "endif")
        input_variables_replaced = []
        for line in input_set_removed:
            results = compiled.finditer(line)
            new_line = line
            offset = 0
            for result in results:
                options = result.groups()
                first = options[0]
                second = options[1]
                if first:
                    name = first
                elif second:
                    name = second
                if name in reserved:
                    continue
                value = variables.get(name)
                if not value:
                    logger.error("Value for variable '{}' not set.".format(name))
                    continue
                len_value = len(value)
                len_name = len(name)
                start = result.start()
                end = result.end()
                beginning = new_line[:offset+start]
                rest = new_line[offset+end:]
                new_line = beginning + value + rest
                offset += len_value - len_name - 1
            input_variables_replaced.append(new_line)

        self.extended_input = '\n'.join(input_variables_replaced)
        self.input_tree = self.inputparser.parse(self.extended_input)

    def determine_file_ids_post_setup(self):
        """Determines the file id's after the CP2K verion has been set
        up. This includes force files, coordinate files, cell files, etc.
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
            self.setup_file_id(file_path, "forces")

        # Determine the presence of an initial coordinate file
        init_coord_file = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_NAME")
        if init_coord_file is not None:
            logger.debug("Initial coordinate file found.")
            # Check against the given files
            file_path = self.search_file(init_coord_file)
            self.setup_file_id(file_path, "initial_coordinates")

        # Determine the presence of a trajectory file
        traj_file = self.input_tree.get_keyword("MOTION/PRINT/TRAJECTORY/FILENAME")
        if traj_file is not None and traj_file != "__STD_OUT__":
            file_format = self.input_tree.get_keyword("MOTION/PRINT/TRAJECTORY/FORMAT")
            extension = {
                "PDB": "pdb",
                "XYZ": "xyz",
                "XMOL": "xyz",
                "ATOMIC": "xyz",
                "DCD": "dcd",
            }[file_format]
            logger.debug("Trajectory file found.")
            normalized_path = self.normalize_cp2k_path(traj_file, extension, "pos")
            file_path = self.search_file(normalized_path)
            self.setup_file_id(file_path, "trajectory")

        # Determine the presence of a cell output file
        cell_motion_file = self.input_tree.get_keyword("MOTION/PRINT/CELL/FILENAME")
        if cell_motion_file is not None:
            logger.debug("Cell file found.")
            extension = "cell"
            normalized_path = self.normalize_cp2k_path(cell_motion_file, extension)
            file_path = self.search_file(normalized_path)
            self.setup_file_id(file_path, "cell_output")

        # Determine the presence of a cell input file
        cell_input_file = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/CELL_FILE_NAME")
        if cell_input_file is not None:
            file_path = self.search_file(cell_input_file)
            self.setup_file_id(file_path, "cell_input")

    def normalize_cp2k_path(self, path, extension, name=""):
        """The paths in CP2K input can be given in many ways. This function
        tries to normalize these paths to a common form.
        """
        if name:
            name = "-" + name
        logger.debug("Normalizing trajectory path")
        project_name = self.input_tree.get_keyword("GLOBAL/PROJECT_NAME")
        if path.startswith("="):
            normalized_path = path[1:]
        elif re.match(r"./", path):
            normalized_path = "{}{}-1.{}".format(path, name, extension)
        else:
            normalized_path = "{}-{}{}-1.{}".format(project_name, path, name, extension)
        return normalized_path

    def search_file(self, path):
        """Searches the list of given files for a file that is defined in the
        CP2K input file.

        First compares the filename, and if multiple matches found descends
        the path until only only one or zero matches found.
        """
        matches = {}
        resolvable = [x for x in self.files.iterkeys() if x not in self.file_ids.itervalues()]

        searched_parts = self.split_path(path)
        for file_path in resolvable:
            available_parts = self.split_path(file_path)
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
            if (sorted_list[0][1] == sorted_list[1][1]):
                logger.error("When searching for file '{}', multiple matches were found. Could not determine which file to use based on their path.")
            else:
                return sorted_list[0][0]

    def split_path(self, path):
        """Splits a path into components and returns them in a reversed order.
        """
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

    # def _Q_energy_total(self):
        # """Return the total energy from the bottom of the input file"""
        # result = Result()
        # result.unit = "hartree"
        # result.value = float(self.regexengine.parse(self.regexs.energy_total, self.parser.get_file_handle("output")))
        # return result

    # def _Q_particle_forces(self):
        # """Return the forces that are controlled by
        # "FORCE_EVAL/PRINT/FORCES/FILENAME". These forces are typicalle printed
        # out during optimization or single point calculation.

        # Supports forces printed in the output file or in a single XYZ file.
        # """
        # result = Result()
        # result.unit = "force_au"

        # # Determine if a separate force file is used or are the forces printed
        # # in the output file.
        # separate_file = True
        # filename = self.input_tree.get_keyword("FORCE_EVAL/PRINT/FORCES/FILENAME")
        # if not filename or filename == "__STD_OUT__":
            # separate_file = False

        # # Look for the forces either in output or in separate file
        # if not separate_file:
            # logger.debug("Looking for forces in output file.")
            # forces = self.regexengine.parse(self.regexs.particle_forces, self.parser.get_file_handle("output"))
            # if forces is None:
                # msg = "No force configurations were found when searching the output file."
                # logger.warning(msg)
                # result.error_message = msg
                # result.code = ResultCode.fail
                # return result

            # # Insert force configuration into the array
            # i_conf = 0
            # force_array = None
            # for force_conf in forces:
                # iterator = self.csvengine.iread(force_conf, columns=(-3, -2, -1), comments=("#", "ATOMIC", "SUM"), separator=None)
                # i_force_array = iterator.next()

                # # Initialize the numpy array if not done yet
                # n_particles = i_force_array.shape[0]
                # n_dim = i_force_array.shape[1]
                # n_confs = len(forces)
                # force_array = np.empty((n_confs, n_particles, n_dim))

                # force_array[i_conf, :, :] = i_force_array
                # i_conf += 1

            # result.value_iterable = force_array
            # return result
        # else:
            # logger.debug("Looking for forces in separate force file.")
            # iterator = self.csvengine.iread(self.parser.get_file_handle("forces"), columns=(-3, -2, -1), comments=("#", "SUM"), separator=r"\ ATOMIC FORCES in \[a\.u\.\]")
            # result.value_iterable = iterator
            # return result

    # def get_initial_atom_positions_and_unit(self):
        # """Returns the starting configuration of the atoms in the system.
        # """
        # unit = "angstrom"

        # # Check where the coordinates are specified
        # coord_format = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_FORMAT")
        # if not coord_format:
            # coord_format = self.input_tree.get_keyword_default("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_FORMAT")

        # # See if the coordinates are provided in the input file
        # if coord_format == "OFF":
            # logger.debug("Using coordinates from the input file.")
            # coords = self.input_tree.get_default_keyword("FORCE_EVAL/SUBSYS/COORD")
            # coords = coords.strip().split('\n')
            # positions = []
            # for line in coords:
                # components = [float(x) for x in line.split()[1:]]
                # positions.append(components)
            # positions = np.array(positions)
            # return positions, unit

        # elif coord_format in ["CP2K", "G96", "XTL", "CRD"]:
            # msg = "Tried to read the number of atoms from the initial configuration, but the parser does not yet support the '{}' format that is used by file '{}'.".format(coord_format, self.parser.file_ids["initial_coordinates"])
            # logger.warning(msg)
        # else:
            # # External file, use AtomsEngine
            # init_coord_file = self.parser.get_file_handle("initial_coordinates")
            # if coord_format == "XYZ":
                # iter_pos = self.atomsengine.iread(init_coord_file, format="xyz")
            # if coord_format == "CIF":
                # iter_pos = self.atomsengine.iread(init_coord_file, format="cif")
            # if coord_format == "PDB":
                # iter_pos = self.atomsengine.iread(init_coord_file, format="pdb")
            # return next(iter_pos), unit

        # # # Check if the unit cell is multiplied programmatically
        # # multiples = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/MULTIPLE_UNIT_CELL")
        # # if not multiples:
            # # multiples = self.input_tree.get_keyword_default("FORCE_EVAL/SUBSYS/TOPOLOGY/MULTIPLE_UNIT_CELL")
        # # factors = [int(x) for x in multiples.split()]
        # # factor = np.prod(np.array(factors))

    # def get_atom_positions_and_unit(self):
        # """Returns the atom positions and unit that were calculated during the
        # simulation.
        # """
        # # Determine the unit
        # unit_path = "MOTION/PRINT/TRAJECTORY/UNIT"
        # unit = self.input_tree.get_keyword(unit_path)
        # # unit = unit.lower()
        # unit = CP2KInput.decode_cp2k_unit(unit)

        # # Read the trajectory
        # traj_file = self.get_file_handle("trajectory", show_warning=False)
        # if not traj_file:
            # logger.debug("No trajectory file detected.")
            # return None, None

        # input_file_format = self.input_tree.get_keyword("MOTION/PRINT/TRAJECTORY/FORMAT")
        # file_format = {
            # "XYZ": "xyz",
            # "XMOL": "xyz",
            # "PDB": "pdb-cp2k",
            # "ATOMIC": "atomic",
        # }.get(input_file_format)

        # if file_format is None:
            # logger.error("Unsupported trajectory file format '{}'.".format(input_file_format))

        # # Use a custom implementation for the CP2K specific weird formats
        # if file_format == "pdb-cp2k":
            # traj_iter = self.csvengine.iread(traj_file, columns=[3, 4, 5], comments=["TITLE", "AUTHOR", "REMARK", "CRYST"], separator="END")
        # elif file_format == "atomic":
            # n_atoms = self.get_result_object("particle_number").value

            # def atomic_generator():
                # conf = []
                # i = 0
                # for line in traj_file:
                    # line = line.strip()
                    # components = np.array([float(x) for x in line.split()])
                    # conf.append(components)
                    # i += 1
                    # if i == n_atoms:
                        # yield np.array(conf)
                        # conf = []
                        # i = 0
            # traj_iter = atomic_generator()
        # else:
            # traj_iter = self.atomsengine.iread(traj_file, format=file_format)

        # # Return the iterator and unit
        # return (traj_iter, unit)

    # def get_functionals(self):
        # """Used to search the input file for a functional definition
        # """
        # # First try to look at the shortcut
        # xc_shortcut = self.input_tree.get_parameter("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL")
        # if xc_shortcut is not None and xc_shortcut != "NONE" and xc_shortcut != "NO_SHORTCUT":
            # logger.debug("Shortcut defined for XC_FUNCTIONAL")

            # # If PBE, check version
            # if xc_shortcut == "PBE":
                # pbe_version = self.input_tree.get_keyword("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/PBE/PARAMETRIZATION")
                # result.value = {
                        # 'ORIG': "GGA_X_PBE",
                        # 'PBESOL': "GGA_X_PBE_SOL",
                        # 'REVPBE': "GGA_X_PBE_R",
                # }.get(pbe_version, "GGA_X_PBE")
                # return result

            # result.value = {
                    # 'B3LYP': "HYB_GGA_XC_B3LYP",
                    # 'BEEFVDW': None,
                    # 'BLYP': "GGA_C_LYP_GGA_X_B88",
                    # 'BP': None,
                    # 'HCTH120': None,
                    # 'OLYP': None,
                    # 'LDA': "LDA_XC_TETER93",
                    # 'PADE': "LDA_XC_TETER93",
                    # 'PBE0': None,
                    # 'TPSS': None,
            # }.get(xc_shortcut, None)
            # return result
        # else:
            # logger.debug("No shortcut defined for XC_FUNCTIONAL. Looking into subsections.")

        # # Look at the subsections and determine what part have been activated

        # # Becke88
        # xc_components = []
        # becke_88 = self.input_tree.get_parameter("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE88")
        # if becke_88 == "TRUE":
            # xc_components.append("GGA_X_B88")

        # # Becke 97
        # becke_97 = self.input_tree.get_parameter("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE97")
        # if becke_97 == "TRUE":
            # becke_97_param = self.input_tree.get_keyword("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE97/PARAMETRIZATION")
            # becke_97_result = {
                    # 'B97GRIMME': None,
                    # 'B97_GRIMME': None,
                    # 'ORIG': "GGA_XC_B97",
                    # 'WB97X-V': None,
            # }.get(becke_97_param, None)
            # if becke_97_result is not None:
                # xc_components.append(becke_97_result)

        # # Return an alphabetically sorted and joined list of the xc components
        # result.value = "_".join(sorted(xc_components))
        # return result

# #===============================================================================
# class CP2K_262_Implementation(CP2KImplementation):
    # def __init__(self, parser):
        # CP2KImplementation.__init__(self, parser)

    # def get_cell(self):
        # """The cell size can be static or dynamic if e.g. doing NPT. If the
        # cell size changes, outputs an Nx3x3 array where N is typically the
        # number of timesteps.

        # Returns:
            # Tuple containing the cell as 3x3 array and the unit.
        # """

        # def cell_generator(cell_file):
            # for line in cell_file:
                # line = line.strip()
                # if line.startswith("#"):
                    # continue
                # split = line.split()
                # A = [float(x) for x in split[2:5]]
                # B = [float(x) for x in split[5:8]]
                # C = [float(x) for x in split[8:11]]
                # result = np.array([A, B, C])*factor
                # yield result, "angstrom"

        # # Determine if the cell is printed during simulation steps
        # cell_output_file = self.get_file_handle("cell_output", show_warning=False)
        # A = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/A")
        # B = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/B")
        # C = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/C")
        # ABC = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/ABC")
        # abg = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/ALPHA_BETA_GAMMA")
        # cell_input_file = self.get_file_handle("cell_input", show_warning=False)

        # # Multiplication factor
        # multiples = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/MULTIPLE_UNIT_CELL")
        # factors = [int(x) for x in multiples.split()]
        # factor = np.prod(np.array(factors))

        # # Separate file from e.g. NPT
        # if cell_output_file:
            # logger.debug("Cell output file found.")
            # result = cell_generator(cell_output_file)
            # return result, "angstrom"

        # # Cartesian cell vectors
        # elif A and B and C:
            # logger.debug("Cartesian cell vectors found.")
            # # Cell given as three vectors
            # A_unit = self.input_tree.get_unit("FORCE_EVAL/SUBSYS/CELL/A")
            # B_unit = self.input_tree.get_unit("FORCE_EVAL/SUBSYS/CELL/B")
            # C_unit = self.input_tree.get_unit("FORCE_EVAL/SUBSYS/CELL/C")

            # A = np.array([float(x) for x in A.split()])
            # B = np.array([float(x) for x in B.split()])
            # C = np.array([float(x) for x in C.split()])

            # # Convert already here as the different vectors may have different units
            # A = convert_unit(A, A_unit)
            # B = convert_unit(B, B_unit)
            # C = convert_unit(C, C_unit)

            # cell = np.empty((3, 3))
            # cell[0, :] = A
            # cell[1, :] = B
            # cell[2, :] = C
            # result = cell*factor
            # return result, "meter"

        # # Cell vector magnitudes and angles
        # elif ABC and abg:
            # logger.debug("Cell vectors defined with angles and magnitudes found.")
            # # Cell given as three vectors
            # ABC_unit = self.input_tree.get_unit("FORCE_EVAL/SUBSYS/CELL/ABC")
            # abg_unit = self.input_tree.get_unit("FORCE_EVAL/SUBSYS/CELL/ALPHA_BETA_GAMMA")

            # angles = np.array([float(x) for x in abg.split()])
            # magnitudes = np.array([float(x) for x in ABC.split()])
            # a = magnitudes[0]
            # b = magnitudes[1]
            # c = magnitudes[2]

            # # Convert angles to radians
            # angles = (angles*ureg(abg_unit)).to(ureg.radian).magnitude
            # alpha = angles[0]
            # beta = angles[1]
            # gamma = angles[2]

            # A = np.array((a, 0, 0))
            # B = np.array((b*math.cos(gamma), b*math.sin(gamma), 0))
            # b_x = B[0]
            # b_y = B[1]
            # c_x = c*math.cos(beta)
            # c_y = 1.0/b_y*(b*c*math.cos(alpha) - b_x*c_x)
            # c_z = math.sqrt(c**2 - c_x**2 - c_y**2)
            # C = np.array((c_x, c_y, c_z))

            # cell = np.zeros((3, 3))
            # cell[0, :] = A
            # cell[1, :] = B
            # cell[2, :] = C
            # result = cell*factor
            # return result, ABC_unit

        # # Separate cell input file
        # elif cell_input_file:
            # logger.debug("Separate cell input file found.")
            # filename = cell_input_file.name
            # if filename.endswith(".cell"):
                # logger.debug("CP2K specific cell input file format found.")
                # result = cell_generator(cell_input_file).next()
                # return result, "angstrom"
            # else:
                # logger.error("The XSC cell file format is not yet supported.")

        # # No cell found
        # else:
            # logger.error("Could not find cell declaration.")
