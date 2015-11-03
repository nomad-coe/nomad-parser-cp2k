#extract! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from cp2kparser.generics.util import *
from cp2kparser.generics.util import *
from cp2kparser.generics.nomadparser import NomadParser
from cp2kparser.implementation.regexs import *
from cp2kparser.engines.regexengine import RegexEngine
from cp2kparser.engines.xyzengine import XYZEngine
from cp2kparser.engines.cp2kinputengine import CP2KInputEngine


#===============================================================================
class CP2KParser(NomadParser):
    """The interface for a NoMaD CP2K parser. All parsing actions will go
    through this class.
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
        self.implementation = globals().get(class_name)(self)
        if self.implementation:
            print_debug("Using version specific implementation '{}'.".format(class_name))
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
        force_path = self.inputengine.get_subsection("FORCE_EVAL/PRINT/FORCES").get_keyword("FILENAME")
        if force_path and force_path != "__STD_OUT__":
            force_path = os.path.basename(force_path) + "-1_0"

        # Check against the given files
        for file_path in resolvable:
            file_no_ext, file_extension = os.path.splitext(file_path)
            if force_path and file_no_ext == force_path and file_extension == ".xyz":
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

    def parse_quantity(self, name):
        """Inherited from NomadParser. The timing and caching is already
        implemented in the superclass.
        """
        # Ask the implementation for the quantity
        result = getattr(self.implementation, name)()
        return result

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
    """

    # The nomad quantities that this implementation supports
    supported_quantities = [
        "energy_total",
        "XC_functional",
        "particle_forces",
    ]

    def __init__(self, parser):
        self.parser = parser
        self.regexs = parser.regexs
        self.regexengine = parser.regexengine
        self.inputengine = parser.inputengine
        self.xyzengine = parser.xyzengine

    def energy_total(self):
        """Return the total energy from the bottom of the input file"""
        return self.regexengine.parse(self.regexs.energy_total, self.parser.get_file_handle("output"))

    def XC_functional(self):
        """Returns the type of the XC functional based on the value of the
        extractor xc_shortcut

                Returns:
                        A string containing the final result that should
                        belong to the list defined in NoMaD wiki.
        """
        # xc_shortcut = self.regexengine.parse(self.regexs.XC_functional, self.parser.get_file_handle("input"))
        xc_shortcut = self.inputengine.get_subsection("FORCE_EVAL/DFT/XC/XC_FUNCTIONAL").get_parameter()

        return {
                'B3LYP': "HYB_GGA_XC_B3LYP",
                'BEEFVDW': "",
                'BLYP': "",
                'PADE': "LDA_XC_TETER93",
                'PBE': "GGA_X_PBE",
        }.get(xc_shortcut, None)

    def particle_forces(self):
        """Return all the forces for every step found.
        """

        # Determine if a separate force file is used or are the forces printed
        # in the output file.
        separate_file = True
        filename = self.inputengine.get_subsection("FORCE_EVAL/PRINT/FORCES").get_keyword("FILENAME")
        if not filename or filename == "__STD_OUT__":
            separate_file = False

        # Look for the forces either in output or in separate file
        if not separate_file:
            print_debug("Looking for forces in output file.")
            forces = self.regexengine.parse(self.regexs.particle_forces, self.parser.get_file_handle("output"))
            forces = unicode("\n".join(forces))
            forces = self.xyzengine.parse_string(forces, (-3, -2, -1), ("#", "ATOMIC", "SUM"))
        else:
            print_debug("Looking for forces in separate force file.")
            forces = self.xyzengine.parse_file(self.parser.get_file_handle("forces"), (-3, -2, -1), ("#", "ATOMIC", "SUM"))
        return forces


#===============================================================================
class CP2K_240_Implementation(CP2KImplementation):
    def __init__(self, parser):
        CP2KImplementation.__init__(self, parser)
