#extract! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from cp2kparser.generics.nomadlogging import *
from cp2kparser.generics.nomadparser import NomadParser
from cp2kparser.implementation.regexs import *
from cp2kparser.engines.regexengine import RegexEngine
from cp2kparser.engines.xyzengine import XYZEngine
from cp2kparser.engines.cp2kinputengine import CP2KInputEngine
import numpy as np


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

        # Engines are created here
        self.inputengine = CP2KInputEngine(self)
        self.xyzengine = XYZEngine(self)
        self.regexengine = RegexEngine(self)

        self.regexs = None
        self.analyse_input_json()
        self.determine_file_ids()
        self.open_files()
        self.setup_version()

    def setup_version(self):
        """Inherited from NomadParser.
        """

        # Determine the CP2K version from the input file
        beginning = self.read_part_of_file("output", 2048)
        version_regex = re.compile(r"CP2K\|\ version\ string:\s+CP2K\ version\ (\d+\.\d+\.\d+)\n")
        version_number = '_' + version_regex.search(beginning).groups()[0].replace('.', '') + '_'

        # Search for a version specific regex class
        class_name = "CP2K{}Regexs".format(version_number)
        self.regexs = globals().get(class_name)
        if self.regexs:
            print_debug("Using version specific regexs '{}'.".format(class_name))
            self.regexs = self.regexs()
        else:
            print_debug("Using default regexs.")
            self.regexs = globals()["CP2KRegexs"]()

        # Search for a version specific implementation
        class_name = "CP2K{}Implementation".format(version_number)
        class_object = globals().get(class_name)
        if class_object:
            print_debug("Using version specific implementation '{}'.".format(class_name))
            self.implementation = class_object(self)
        else:
            print_debug("Using default implementation.")
            self.implementation = globals()["CP2KImplementation"](self)

    def read_part_of_file(self, file_id, size=1024):
        fh = self.file_handles[file_id]
        fh.seek(0, os.SEEK_SET)
        buffer = fh.read(size)
        return buffer

    def determine_file_ids(self):
        """Inherited from NomadParser.
        """

        # Determine a list of filepaths that need id resolution
        resolved = {}
        resolvable = []
        for file_object in self.files:
            path = file_object.get("path")
            file_id = file_object.get("file_id")
            if not file_id:
                resolvable.append(path)
            else:
                resolved[file_id] = path

        # First resolve the file that can be identified by extension
        input_path = resolved.get("input")
        if not input_path:
            for file_path in resolvable:
                if file_path.endswith(".inp"):
                    self.file_ids["input"] = file_path
                    self.get_file_handle("input")
                if file_path.endswith(".out"):
                    self.file_ids["output"] = file_path

        # Now check from input what the other files are called
        self.inputengine.parse_input()
        force_path = self.inputengine.get_keyword("FORCE_EVAL/PRINT/FORCES/FILENAME")
        project_name = self.inputengine.get_keyword("GLOBAL/PROJECT_NAME")
        if force_path is not None and force_path != "__STD_OUT__":

            # The force path is not typically exactly as written in input
            if force_path.startswith("="):
                print_debug("Using single force file.")
                force_path = force_path[1:]
            elif re.match(r".?/", force_path):
                print_debug("Using separate force file for each step.")
                force_path = "{}-1_0.xyz".format(force_path)
            else:
                print_debug("Using separate force file for each step.")
                force_path = "{}-{}-1_0.xyz".format(project_name, force_path)
            force_path = os.path.basename(force_path)

        # Check against the given files
        for file_path in resolvable:
            tail = os.path.basename(file_path)
            if force_path is not None and tail == force_path:
                self.file_ids["forces"] = file_path
                self.get_file_handle("forces")

    def open_files(self):
        """Open the file handles and keep them open until program finishes.
        """
        for file_id, file_path in self.file_ids.iteritems():
            try:
                file_handle = open(file_path, 'r')
            except (OSError, IOError):
                print_error("Could not open file: '{}'".format(file_path))
            else:
                self.file_handles[file_id] = file_handle

    def get_unformatted_quantity(self, name):
        """Inherited from NomadParser. The timing and caching is already
        implemented in the superclass.
        """
        # Ask the implementation for the quantity
        function = getattr(self.implementation, "_Q_" + name)
        if function:
            return function()
        else:
            print_error("The function for quantity '{}' is not defined".format(name))

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
        self.inputengine = parser.inputengine
        self.xyzengine = parser.xyzengine

    def _Q_energy_total(self):
        """Return the total energy from the bottom of the input file"""
        return self.regexengine.parse(self.regexs.energy_total, self.parser.get_file_handle("output"))

    def _Q_XC_functional(self):
        """Returns the type of the XC functional.

        Can currently only determine version if they are declared as parameters
        for XC_FUNCTIONAL or via activating subsections of XC_FUNCTIONAL.

        Returns:
            A string containing the final result that should
            belong to the list defined in NoMaD wiki.
        """

        # First try to look at the shortcut
        xc_shortcut = self.inputengine.get_subsection("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL").get_parameter()
        if xc_shortcut is not None and xc_shortcut != "NONE" and xc_shortcut != "NO_SHORTCUT":
            print_debug("Shortcut defined for XC_FUNCTIONAL")

            # If PBE, check version
            if xc_shortcut == "PBE":
                pbe_version = self.inputengine.get_subsection("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/PBE").get_keyword("PARAMETRIZATION")
                return {
                        'ORIG': "GGA_X_PBE",
                        'PBESOL': "GGA_X_PBE_SOL",
                        'REVPBE': "GGA_X_PBE_R",
                }.get(pbe_version, "GGA_X_PBE")

            return {
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
        else:
            print_debug("No shortcut defined for XC_FUNCTIONAL. Looking into subsections.")

        # Look at the subsections and determine what part have been activated

        # Becke88
        xc_components = []
        becke_88 = self.inputengine.get_subsection("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE88").get_parameter()
        if becke_88 == "TRUE":
            xc_components.append("GGA_X_B88")

        # Becke 97
        becke_97 = self.inputengine.get_parameter("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE97")
        if becke_97 == "TRUE":
            becke_97_param = self.inputengine.get_keyword("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/BECKE97/PARAMETRIZATION")
            becke_97_result = {
                    'B97GRIMME': None,
                    'B97_GRIMME': None,
                    'ORIG': "GGA_XC_B97",
                    'WB97X-V': None,
            }.get(becke_97_param, None)
            if becke_97_result is not None:
                xc_components.append(becke_97_result)

        # Return an alphabetically sorted and joined list of the xc components
        return "_".join(sorted(xc_components))

    def _Q_particle_forces(self):
        """Return all the forces for every step found.

        Supports forces printed in the output file or in a single .xyz file.
        """

        # Determine if a separate force file is used or are the forces printed
        # in the output file.
        separate_file = True
        filename = self.inputengine.get_keyword("FORCE_EVAL/PRINT/FORCES/FILENAME")
        if not filename or filename == "__STD_OUT__":
            separate_file = False

        # Look for the forces either in output or in separate file
        if not separate_file:
            print_debug("Looking for forces in output file.")
            forces = self.regexengine.parse(self.regexs.particle_forces, self.parser.get_file_handle("output"))
            if forces is None:
                print_warning("No forces could be found in the output file.")
                return None

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

            return force_array
        else:
            print_debug("Looking for forces in separate force file.")
            forces = self.xyzengine.parse(self.parser.get_file_handle("forces"), columns=(-3, -2, -1), comments=("#", "ATOMIC", "SUM"), separator=r"\ ATOMIC FORCES in \[a\.u\.\]")
            if forces is None:
                print print_warning("No forces could be found in the XYZ file.")
        return forces


#===============================================================================
class CP2K_262_Implementation(CP2KImplementation):
    def __init__(self, parser):
        CP2KImplementation.__init__(self, parser)
