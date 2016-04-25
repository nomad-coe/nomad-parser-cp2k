#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides functions for creating a python object representing a CP2K input
structure.

Creates preparsed versions of the cp2k_input.xmls and pickles them (python
version of serialization). The pickle files can then be easily reused without
doing the xml parsing again.

The actual calculation input contents can later be added to this object. Then
the object can be queried for the results, or the default values defined by the
cp2k_input.xml.
"""

import xml.etree.cElementTree as ET
import logging
import cPickle as pickle
from cp2kparser.generic.inputparsing import *
logger = logging


#===============================================================================
def generate_object_tree(xml_file):

    xml_element = ET.parse(xml_file)
    object_tree = recursive_tree_generation(xml_element)
    return object_tree


#===============================================================================
def recursive_tree_generation(xml_element):

    # Make new section object for the root
    section_name_element = xml_element.find("NAME")
    if section_name_element is not None:
        section_name = section_name_element.text
    else:
        section_name = "CP2K_INPUT"
    section = Section(section_name)

    # Section parameters
    parameter = xml_element.find("SECTION_PARAMETERS")
    if parameter:
        sp_default_element = parameter.find("DEFAULT_VALUE")
        sp_default_value = None
        if sp_default_element is not None:
            sp_default_value = sp_default_element.text
        sp_lone_element = parameter.find("LONE_KEYWORD_VALUE")
        sp_lone_value = None
        if sp_lone_element is not None:
            sp_lone_value = sp_lone_element.text
        parameter_object = SectionParameters(sp_default_value, sp_lone_value)
        section.section_parameter = parameter_object

    # Keywords
    for keyword in xml_element.findall("KEYWORD"):
        keyword_names = keyword.findall("NAME")
        default_name = None
        aliases = []
        for name in keyword_names:
            keytype = name.get("type")
            if keytype == "default":
                default_name = name.text
            else:
                aliases.append(name.text)
        default_keyword_element = keyword.find("DEFAULT_VALUE")
        default_keyword_value = None
        if default_keyword_element is not None:
            default_keyword_value = default_keyword_element.text

        default_unit_element = keyword.find("DEFAULT_UNIT")
        default_unit_value = None
        if default_unit_element is not None:
            default_unit_value = default_unit_element.text

        keyword_object = Keyword(default_name, default_keyword_value, default_unit_value)
        section.keywords[default_name].append(keyword_object)
        for alias in aliases:
            section.keywords[alias].append(keyword_object)

    # Sections
    for sub_section_element in xml_element.findall("SECTION"):
        sub_section = recursive_tree_generation(sub_section_element)
        section.sections[sub_section.name].append(sub_section)

    # Return section
    return section

#===============================================================================
# Run main function by default
if __name__ == "__main__":
    xml_file = open("../versions/cp2k262/input_data/cp2k_input.xml", 'r')
    object_tree = CP2KInput(generate_object_tree(xml_file))
    file_name = "../versions/cp2k262/input_data/cp2k_input_tree.pickle"
    fh = open(file_name, "wb")
    pickle.dump(object_tree, fh, protocol=2)
