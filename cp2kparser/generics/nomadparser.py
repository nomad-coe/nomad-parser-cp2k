#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import time
from cp2kparser.generics.util import *


#===============================================================================
class NomadParser(object):
    """The base class for a NoMaD parser.
    """

    def __init__(self, input_json_string):
        self.input_json_string = input_json_string
        self.input_json_object = None
        self.files = {}
        self.tmp_dir = None
        self.metainfo_to_keep = None
        self.metainfo_to_skip = None
        self.file_ids = {}
        self.file_handles = {}
        self.interface_object = None
        self.implementation = None
        self.file_contents = {}
        self.file_sizes = {}
        self.results = {}

    def get_file_contents(self, file_id):

        cache_limit = 10000
        contents = self.file_contents.get(file_id)
        if not contents:
            fh = self.file_handles[file_id]
            fh.seek(0)
            contents = fh.read()
            if self.get_file_size(file_id) <= cache_limit:
                self.file_contents[file_id] = contents
        return contents

    def get_file_size(self, file_id):

        size = self.file_sizes.get(file_id)
        if not size:
            fh = self.file_handles[file_id]
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            self.file_sizes[file_id] = size
        return size

    def get_file_handle(self, file_id):

        handle = self.file_handles.get(file_id)
        if not handle:

            path = self.file_ids[file_id]
            try:
                handle = open(path, "r")
            except (OSError, IOError):
                print_error("Could not open file: '{}'".format(path))
            else:
                self.file_handles[file_id] = handle
        handle.seek(0, os.SEEK_SET)
        return handle

    def analyse_input_json(self):

        # Try to decode
        self.input_json_object = json.loads(self.input_json_string)

        # See if the needed attributes exist
        self.tmp_dir = self.input_json_object.get("tmpDir")
        if self.tmp_dir is None:
            print_error("No temporary folder specified.")
        self.files = self.input_json_object.get("files")
        if self.files is None:
            print_error("No files specified.")
        self.metainfo_to_keep = self.input_json_object.get("metainfoToKeep")
        self.metainfo_to_skip = self.input_json_object.get("metainfoToSkip")

        # See if the metainfos exist

    def setup_version(self):
        """Setup a correct implementation for this version of CP2K.
        """
        pass

    def determine_file_ids(self):
        """If the files have not been given an id, try to determine the
        correct ids by looking at the input file, contents and file extensions.
        """
        pass

    def get_quantity(self, name):
        """Given a unique quantity id which is present in the metainfo
        declaration, parses the corresponding quantity (if available) and
        return the value as json.
        """
        # Start timing
        print_debug(74*'-')
        print_debug("Getting quantity '{}'".format(name))
        start = time.clock()

        #Check availability
        available = self.check_quantity_availability(name)
        if not available:
            print_warning("The quantity '{}' is not available for this parser version.".format(name))
            return

        # Check cache
        result = self.results.get(name)
        if not result:
            # Ask the engine for the quantity
            result = self.parse_quantity(name)
            self.results[name] = result
            if result is None:
                print_debug("The quantity '{}' could not be succesfully parsed.".format(name))
        else:
            print_debug("Using cached result.")

        stop = time.clock()
        print_debug("Elapsed time: {} ms".format((stop-start)*1000))
        return result

    def parse_quantity(self, name):
        """Override this function in an actual implementation"""
        pass

    def check_quantity_availability(self, name):
        """Check quantity availability.

          -Check the list of available quantities declared in interface.
          -Check if the run type actually produces the quantity
          -Check if the quantity is allowed by the 'metainfoToKeep' and
          'metainfoToSkip'
        """
        return True
