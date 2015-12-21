import re
from cp2kparser.generics.parserbuilder import ParserBuilder
from cp2kparser.implementation.implementations import *
import logging
import sys
logger = logging.getLogger(__name__)


#===============================================================================
class CP2KParserBuilder(ParserBuilder):
    """Builds the correct parser by looking at the given files and the given
    input.

    This class handles the initial setup before any parsing can happen. It
    determines which version of the software was used and then sets up a
    correct implementation.
    """
    def __init__(self, input_json_string, stream=sys.stdout):
        ParserBuilder.__init__(self, input_json_string, stream=sys.stdout)

    def build_parser(self):
        """Setups the version by looking at the output file and the version
        specified in it.
        """
        # Search for the output file
        count = 0
        for filepath in self.parser_context.files.iterkeys():
            if filepath.endswith(".out"):
                count += 1
                outputpath = filepath
        if count > 1:
            logger("Could not determine the correct outputfile because multiple files with extension '.out' were found.")
            return
        elif count == 0:
            logger.error("No output file could be found. The outputfile should have a '.out' extension.")
            return

        # Search for the version specification
        outputfile = open(outputpath, 'r')
        regex = re.compile(r" CP2K\| version string:\s+CP2K version ([\d\.]+)")
        for line in outputfile:
            result = regex.match(line)
            if result:
                self.parser_context.version_id = result.group(1).replace('.', '')
                break

        # Search for a version specific implementation
        class_name = "CP2KImplementation{}".format(self.parser_context.version_id)
        class_object = globals().get(class_name)
        if class_object:
            logger.debug("Using version specific implementation '{}'.".format(class_name))
            self.implementation = class_object(self.parser_context)
        else:
            logger.debug("No version specific implementation found. Using the default implementation: {}".format(class_name))
            self.parser_context.version_id = "262"
            self.implementation = globals()["CP2KImplementation262"](self.parser_context)

        return self.implementation















        # self.inputengine.setup_version_number(self.version_number)
        # self.input_tree = self.inputengine.parse(self.extended_input)
        # Search for a version specific regex class
        # class_name = "CP2K{}Regexs".format(version_name)
        # self.regexs = globals().get(class_name)
        # if self.regexs:
            # logger.debug("Using version specific regexs '{}'.".format(class_name))
            # self.regexs = self.regexs()
        # else:
            # logger.debug("Using default regexs.")
            # self.regexs = globals()["CP2KRegexs"]()

    # def determine_file_ids_pre_setup(self):
        # """First resolve the files that can be identified by extension.
        # """
        # # Input and output files
        # for file_path in self.files.iterkeys():
            # if file_path.endswith(".inp"):
                # self.setup_file_id(file_path, "input")
            # if file_path.endswith(".out"):
                # self.setup_file_id(file_path, "output")

        # # Include files
        # input_file = self.get_file_contents("input")
        # for line in input_file.split("\n"):
            # line = line.strip()
            # if line.startswith("@INCLUDE") or line.startswith("@include"):
                # split = line.split(None, 1)
                # filename = split[1]
                # if filename.startswith(('\"', '\'')) and filename.endswith(('\"', '\'')):
                    # filename = filename[1:-1]
                # filepath = self.search_file(filename)
                # self.setup_file_id(filepath, "include")

    # def parse(self):
        # self.implementation.parse()

    # def get_all_quantities(self):
        # """Parse all supported quantities."""
        # for method in self.get_supported_quantities:
            # self.get_quantity(method)

    # def start_parsing(self, name):
        # """Inherited from NomadParser.
        # """
        # # Ask the implementation for the quantity
        # function = getattr(self.implementation, "_Q_" + name)
        # if function:
            # return function()
        # else:
            # logger.error("The function for quantity '{}' is not defined".format(name))

    # def get_supported_quantities(self):
        # """Inherited from NomadParser.
        # """
        # supported_quantities = []
        # implementation_methods = [method for method in dir(self.implementation) if callable(getattr(self.implementation, method))]
        # for method in implementation_methods:
            # if method.startswith("_Q_"):
                # method = method[3:]
                # supported_quantities.append(method)

        # return supported_quantities


# #===============================================================================
# class CP2KImplementation(object):
    # """Defines the basic functions that are used to map results to the
    # corresponding NoMaD quantities.

    # This class provides the basic implementations and for a version specific
    # updates and additions please make a new class that inherits from this.

    # The functions that return certain quantities are tagged with a prefix '_Q_'
    # to be able to automatically determine which quantities have at least some
    # level of support. With the tag they can be also looped through.
    # """
    # def __init__(self, parser):
        # self.parser = parser
        # self.regexs = parser.regexs
        # self.regexengine = parser.regexengine
        # self.csvengine = parser.csvengine
        # self.atomsengine = parser.atomsengine
        # self.input_tree = parser.input_tree

        # # Define the output parsing tree for this version
        # self.outputstructure = SM(
            # name='root',
            # startReStr="",
            # subMatchers=[
                # SM(
                    # name='new_run',
                    # startReStr=r" DBCSR\| Multiplication driver",
                    # endReStr="[.\*]+PROGRAM STOPPED IN",
                    # required=True,
                    # sections=['section_run'],
                    # subMatchers=[
                        # SM(
                            # name="run_datetime",
                            # startReStr=r"[\*\s]+PROGRAM STARTED AT\s+(?P<cp2k_run_start_date>\d{4}-\d{2}-\d{2}) (?P<cp2k_run_start_time>\d{2}:\d{2}:\d{2}.\d{3})",
                        # ),
                        # SM(
                            # name="version",
                            # startReStr=r" CP2K\| version string:\s+(?P<program_version>[\w\d\W\s]+)",
                        # ),
                        # SM(
                            # name="svn_revision",
                            # startReStr=r" CP2K\| source code revision number:\s+svn:(?P<cp2k_svn_revision>\d+)",
                        # ),
                        # SM(
                            # name="cell",
                            # startReStr=" CELL\|",
                            # forwardMatch=True,
                            # subMatchers=[
                                # SM(
                                    # name="cell_a",
                                    # startReStr=" CELL\| Vector a \[angstrom\]:\s+(?P<cp2k_cell_vector_a>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                                # ),
                                # SM(
                                    # name="cell_b",
                                    # startReStr=" CELL\| Vector b \[angstrom\]:\s+(?P<cp2k_cell_vector_b>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                                # ),
                                # SM(
                                    # name="cell_c",
                                    # startReStr=" CELL\| Vector c \[angstrom\]:\s+(?P<cp2k_cell_vector_c>[\d\.]+\s+[\d\.]+\s+[\d\.]+)+"
                                # ),
                            # ]
                        # )
                    # ]
                # )
            # ]
        # )

        # # The cache settings
        # self.cachingLevelForMetaName = {
            # 'cp2k_cell_vector_a': CachingLevel.Cache,
            # 'cp2k_cell_vector_b': CachingLevel.Cache,
            # 'cp2k_cell_vector_c': CachingLevel.Cache,
        # }

    # def parse(self):
        # """Parses everything that can be found from the given files. The
        # results are outputted to std.out by using the backend. The scala layer
        # will the take on from that.
        # """
        # # Write the starting bracket
        # self.parser.stream.write("[")

        # # Use the SimpleMatcher to extract most of the results
        # parserInfo = {"name": "cp2k-parser", "version": "1.0"}
        # outputfilename = self.parser.get_file_handle("output").name
        # metainfoenv = self.parser.metainfoenv
        # backend = self.parser.backend
        # outputstructure = self.outputstructure
        # self.parser.parse_file(outputfilename, outputstructure, metainfoenv, backend, parserInfo, self.cachingLevelForMetaName)

        # # Then extract the things that cannot be extracted by the SimpleMatcher

        # # Write the ending bracket
        # self.parser.stream.write("]\n")

    # # def dateconverter(datestring):

    # def _Q_energy_total(self):
        # """Return the total energy from the bottom of the input file"""
        # result = Result()
        # result.unit = "hartree"
        # result.value = float(self.regexengine.parse(self.regexs.energy_total, self.parser.get_file_handle("output")))
        # return result

    # def _Q_XC_functional(self):
        # """Returns the type of the XC functional.

        # Can currently only determine version if they are declared as parameters
        # for XC_FUNCTIONAL or via activating subsections of XC_FUNCTIONAL.

        # Returns:
            # A string containing the final result that should
            # belong to the list defined in NoMaD wiki.
        # """
        # result = Result()

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

    # def _Q_particle_number(self):
        # """Return the number of particles in the system.

        # CP2K output doesn't automatically print the number of atoms. For this
        # reason this function has to look at the initial configuration and
        # calculate the number from it. The initial configuration is something
        # that must be present for all calculations.
        # """
        # result = Result()
        # result.cache = True

        # # Check where the coordinates are specified
        # coord_format = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_FORMAT")
        # if not coord_format:
            # coord_format = self.input_tree.get_keyword_default("FORCE_EVAL/SUBSYS/TOPOLOGY/COORD_FILE_FORMAT")

        # # Check if the unit cell is multiplied programmatically
        # multiples = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/TOPOLOGY/MULTIPLE_UNIT_CELL")
        # if not multiples:
            # multiples = self.input_tree.get_keyword_default("FORCE_EVAL/SUBSYS/TOPOLOGY/MULTIPLE_UNIT_CELL")
        # factors = [int(x) for x in multiples.split()]
        # factor = np.prod(np.array(factors))

        # # See if the coordinates are provided in the input file
        # if coord_format == "OFF":
            # logger.debug("Using coordinates from the input file.")
            # coords = self.input_tree.get_default_keyword("FORCE_EVAL/SUBSYS/COORD")
            # coords.strip()
            # n_particles = coords.count("\n")
            # result.value = factor*n_particles
        # elif coord_format in ["CP2K", "G96", "XTL", "CRD"]:
            # msg = "Tried to read the number of atoms from the initial configuration, but the parser does not yet support the '{}' format that is used by file '{}'.".format(coord_format, self.parser.file_ids["initial_coordinates"])
            # logger.warning(msg)
            # result.error_message = msg
            # result.code = ResultCode.fail
        # else:
            # # External file, use AtomsEngine
            # init_coord_file = self.parser.get_file_handle("initial_coordinates")
            # if coord_format == "XYZ":
                # n_particles = self.atomsengine.n_atoms(init_coord_file, format="xyz")
            # if coord_format == "CIF":
                # n_particles = self.atomsengine.n_atoms(init_coord_file, format="cif")
            # if coord_format == "PDB":
                # n_particles = self.atomsengine.n_atoms(init_coord_file, format="pdb")

        # result.value = factor*n_particles
        # return result

    # def _Q_particle_position(self):
        # """Returns the particle positions (trajectory).
        # """
        # result = Result()

        # # Determine the unit
        # unit_path = "MOTION/PRINT/TRAJECTORY/UNIT"
        # unit = self.input_tree.get_keyword(unit_path)
        # unit = unit.lower()
        # result.unit = CP2KInput.decode_cp2k_unit(unit)

        # # Read the trajectory
        # traj_file = self.parser.get_file_handle("trajectory")
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
            # traj_iter = self.parser.csvengine.iread(traj_file, columns=[3, 4, 5], comments=["TITLE", "AUTHOR", "REMARK", "CRYST"], separator="END")
        # elif file_format == "atomic":
            # n_atoms = self.parser.get_result_object("particle_number").value

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

        # # Return the iterator
        # result.value_iterable = traj_iter
        # return result

    # def _Q_cell(self):
        # """The cell size can be static or dynamic if e.g. doing NPT. If the
        # cell size changes, outputs an Nx3x3 array where N is typically the
        # number of timesteps.
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
                # yield result

        # result = Result()

        # # Determine if the cell is printed during simulation steps
        # cell_output_file = self.parser.get_file_handle("cell_output")
        # A = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/A")
        # B = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/B")
        # C = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/C")
        # ABC = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/ABC")
        # abg = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/ALPHA_BETA_GAMMA")
        # cell_input_file = self.parser.get_file_handle("cell_input")

        # # Multiplication factor
        # multiples = self.input_tree.get_keyword("FORCE_EVAL/SUBSYS/CELL/MULTIPLE_UNIT_CELL")
        # factors = [int(x) for x in multiples.split()]
        # factor = np.prod(np.array(factors))

        # # Separate file from e.g. NPT
        # if cell_output_file:
            # logger.debug("Cell output file found.")
            # result.unit = "angstrom"
            # result.value_iterable = cell_generator(cell_output_file)
            # return result

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
            # result.value = cell*factor
            # return result

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
            # result.value = cell*factor
            # result.unit = ABC_unit
            # return result

        # # Separate cell input file
        # elif cell_input_file:
            # logger.debug("Separate cell input file found.")
            # filename = cell_input_file.name
            # if filename.endswith(".cell"):
                # logger.debug("CP2K specific cell input file format found.")
                # result.value = cell_generator(cell_input_file).next()
                # result.unit = "angstrom"
                # return result
            # else:
                # logger.error("The XSC cell file format is not yet supported.")

        # # No cell found
        # else:
            # logger.error("Could not find cell declaration.")


# #===============================================================================
# class CP2K_262_Implementation(CP2KImplementation):
    # def __init__(self, parser):
        # CP2KImplementation.__init__(self, parser)
