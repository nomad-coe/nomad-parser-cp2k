import os
import re
from cp2kparser.generics.nomadparser import NomadParser, Result
from cp2kparser.implementation.regexs import *
from cp2kparser.engines.regexengine import RegexEngine
from cp2kparser.engines.xyzengine import XYZEngine
from cp2kparser.engines.cp2kinputengine import CP2KInputEngine
from cp2kparser.engines.xmlengine import XMLEngine
import numpy as np
import logging
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
    def __init__(self, input_json_string):
        NomadParser.__init__(self, input_json_string)

        self.version_number = None

        # Engines are created here
        self.xyzengine = XYZEngine(self)
        self.regexengine = RegexEngine(self)
        self.xmlengine = XMLEngine(self)
        self.inputengine = CP2KInputEngine()

        self.input_tree = None
        self.regexs = None
        self.analyse_input_json()
        self.check_resolved_file_ids()
        self.determine_file_ids_from_extension()
        self.setup_version()
        self.determine_file_ids()
        # self.open_files()

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

    def read_part_of_file(self, file_id, size=1024):
        fh = self.file_handles[file_id]
        fh.seek(0, os.SEEK_SET)
        buffer = fh.read(size)
        return buffer

    def check_resolved_file_ids(self):
        """Save the file id's that were given in the JSON input.
        """
        resolved = {}
        resolvable = []
        for file_object in self.files:
            path = file_object.get("path")
            file_id = file_object.get("file_id")
            if not file_id:
                resolvable.append(path)
            else:
                resolved[file_id] = path

        for id, path in resolved.iteritems():
            self.file_ids[id] = path
            self.get_file_handle(id)

        self.resolvable = resolvable

    def determine_file_ids_from_extension(self):
        """First resolve the files that can be identified by extension.
        """
        for file_path in self.resolvable:
            if file_path.endswith(".inp"):
                self.file_ids["input"] = file_path
                self.get_file_handle("input")
            if file_path.endswith(".out"):
                self.file_ids["output"] = file_path
                self.get_file_handle("output")

    def determine_file_ids(self):
        """Inherited from NomadParser.
        """
        # Check from input what the other files are called
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
        for file_path in self.resolvable:
            tail = os.path.basename(file_path)
            if force_path is not None and tail == force_path:
                self.file_ids["forces"] = file_path
                self.get_file_handle("forces")

    # def open_files(self):
        # """Open the file handles and keep them open until program finishes.
        # """
        # for file_id, file_path in self.file_ids.iteritems():
            # try:
                # file_handle = open(file_path, 'r')
            # except (OSError, IOError):
                # logger.error("Could not open file: '{}'".format(file_path))
            # else:
                # self.file_handles[file_id] = file_handle

    def get_quantity_unformatted(self, name):
        """Inherited from NomadParser. The timing and caching is already
        implemented in the superclass.
        """
        # Ask the implementation for the quantity
        function = getattr(self.implementation, "_Q_" + name)
        if function:
            return function()
        else:
            logger.error("The function for quantity '{}' is not defined".format(name))

    def check_quantity_availability(self, name):
        """Inherited from NomadParser.
        """
        #TODO
        return True


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
        self.xyzengine = parser.xyzengine
        self.input_tree = parser.input_tree

    def _Q_energy_total(self):
        """Return the total energy from the bottom of the input file"""
        result = Result()
        result.kind = Result.energy
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
        result.kind = Result.text

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
        """Return all the forces for every step found.

        Supports forces printed in the output file or in a single .xyz file.
        """
        result = Result()
        result.kind = Result.force
        result.unit = ureg.force_au

        # Determine if a separate force file is used or are the forces printed
        # in the output file.
        separate_file = True
        filename = self.input_tree.get_keyword("FORCE_EVAL/PRINT/FORCES/FILENAME")
        if not filename or filename == "__STD_OUT__":
            separate_file = False

        # Look for the forces either in output or in separate file
        if not separate_file:
            logger.debug("Looking for forcesnature in output file.")
            forces = self.regexengine.parse(self.regexs.particle_forces, self.parser.get_file_handle("output"))
            if forces is None:
                logger.warning("No forces could be found in the output file.")
                result.value = forces
                return result

            # Insert force configuration into the array
            i_conf = 0
            force_array = None
            for force_conf in forces:
                i_force_array = self.xyzengine.parse(force_conf, columns=(-3, -2, -1), comments=("#", "ATOMIC", "SUM"), separator=None)
                i_force_array = i_force_array[0]

                # Initialize the numpy array if not done yet
                n_particles = i_force_array.shape[0]
                n_dim = i_force_array.shape[1]
                n_confs = len(forces)
                force_array = np.empty((n_confs, n_particles, n_dim))

                force_array[i_conf, :, :] = i_force_array
                i_conf += 1

            result.value = force_array
            return result
        else:
            logger.debug("Looking for forces in separate force file.")
            forces = self.xyzengine.parse(self.parser.get_file_handle("forces"), columns=(-3, -2, -1), comments=("#", "ATOMIC", "SUM"), separator=r"\ ATOMIC FORCES in \[a\.u\.\]")
            if forces is None:
                logger.warning("No forces could be found in the XYZ file.")

        result.value = forces
        return result


#===============================================================================
class CP2K_262_Implementation(CP2KImplementation):
    def __init__(self, parser):
        CP2KImplementation.__init__(self, parser)
