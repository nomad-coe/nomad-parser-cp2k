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
import json
import cPickle as pickle
from cp2kparser.generic.inputparsing import *
logger = logging


#===============================================================================
def generate_object_tree(xml_file, for_metainfo=False):

    xml_element = ET.parse(xml_file)

    # Leave out certain currently uninteresting parts of the input. These can be
    # added later if need be.
    root = xml_element.getroot()
    # ignored = ["ATOM", "DEBUG", "EXT_RESTART", "FARMING", "OPTIMIZE_BASIS", "OPTIMIZE_INPUT", "SWARM", "TEST"]
    # removed = []
    # for child in root:
        # name = child.find("NAME")
        # if name is not None:
            # name_string = name.text
            # if name_string in ignored:
                # removed.append(child)
    # for child in removed:
        # root.remove(child)

    # Recursively generate the tree
    object_tree = recursive_tree_generation(root, for_metainfo)
    return object_tree


#===============================================================================
def recursive_tree_generation(xml_element, for_metainfo=False, name_stack=[]):

    # Make new section object for the root
    section_name_element = xml_element.find("NAME")
    if section_name_element is not None:
        section_name = section_name_element.text
    else:
        section_name = "CP2K_INPUT"
    section = Section(section_name)

    # Ignore sections that control the print settings
    ignored = ["EACH", "PRINT"]
    if section_name in ignored:
        return

    if for_metainfo:
        # Descriptions
        description = xml_element.find("DESCRIPTION")
        if description is not None:
            section.description = description.text

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

        # Data type
        data_type = parameter.find("DATA_TYPE")
        if data_type is not None:
            data_type_kind = data_type.get("kind")
            parameter_object.data_type = data_type_kind

            # Data dimension
            data_dim = data_type.find("N_VAR")
            if data_dim is not None:
                parameter_object.data_dimension = data_dim.text

        if for_metainfo:
            # Description
            section_param_description = parameter.find("DESCRIPTION")
            if section_param_description is not None:
                parameter_object.description = section_param_description.text

    # Default keyword
    default_keyword_element = xml_element.find("DEFAULT_KEYWORD")
    if default_keyword_element is not None:
        default_keyword_object = DefaultKeyword()

        # Data type
        data_type = default_keyword_element.find("DATA_TYPE")
        if data_type is not None:
            data_type_kind = data_type.get("kind")
            default_keyword_object.data_type = data_type_kind

            # Data dimension
            data_dim = data_type.find("N_VAR")
            if data_dim is not None:
                default_keyword_object.data_dimension = data_dim.text

        if for_metainfo:
            # Description
            description = default_keyword_element.find("DESCRIPTION")
            if description is not None:
                default_keyword_object.description = description.text

        section.default_keyword = default_keyword_object

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

        # Ignore hidden keywords
        if default_name.startswith("__"):
            continue

        # Save the default keyword name
        section.default_keyword_names.append(default_name)

        default_keyword_element = keyword.find("DEFAULT_VALUE")
        default_keyword_value = None
        if default_keyword_element is not None:
            default_keyword_value = default_keyword_element.text

        default_unit_element = keyword.find("DEFAULT_UNIT")
        default_unit_value = None
        if default_unit_element is not None:
            default_unit_value = default_unit_element.text

        keyword_object = Keyword(default_name, default_keyword_value, default_unit_value, default_name)
        section.keywords[default_name].append(keyword_object)
        for alias in aliases:
            section.keywords[alias].append(keyword_object)

        # Data type
        data_type = keyword.find("DATA_TYPE")
        if data_type is not None:
            data_type_kind = data_type.get("kind")
            keyword_object.data_type = data_type_kind

            # Data dimension
            data_dim = data_type.find("N_VAR")
            if data_dim is not None:
                keyword_object.data_dimension = data_dim.text

        if for_metainfo:
            # Description
            keyword_description = keyword.find("DESCRIPTION")
            if keyword_description is not None:
                keyword_object.description = keyword_description.text

    # Sections
    for sub_section_element in xml_element.findall("SECTION"):
        sub_section = recursive_tree_generation(sub_section_element, for_metainfo)
        if sub_section is not None:
            section.sections[sub_section.name].append(sub_section)

    # Return section
    return section


#===============================================================================
def generate_input_metainfos(object_tree):
    parent = Section("dummy")
    root_section = object_tree.root_section
    root_section.name = "CP2K_INPUT"
    root_section.description = "The section containing all information that is explicitly stated in the CP2K input file. The sections that control printing (PRINT, EACH) and the hidden input keywords starting with a double underscore are not included."
    container = []
    name_stack = []
    generate_metainfo_recursively(root_section, parent, container, name_stack)
    with open("input_metainfo.json", "w") as f:
        f.write(json.dumps(container, indent=2, separators=(',', ': ')))


#===============================================================================
def generate_metainfo_recursively(obj, parent, container, name_stack):

    json = None
    if isinstance(obj, Section):
        name_stack.append(obj.name)
        json = generate_section_metainfo_json(obj, parent, name_stack)
        for child in obj.sections.itervalues():
            generate_metainfo_recursively(child[0], obj, container, name_stack)
        for child in obj.keywords.itervalues():
            generate_metainfo_recursively(child[0], obj, container, name_stack)
        if obj.section_parameter is not None:
            generate_metainfo_recursively(obj.section_parameter, obj, container, name_stack)
        if obj.default_keyword is not None:
            generate_metainfo_recursively(obj.default_keyword, obj, container, name_stack)
        name_stack.pop()
    else:
        json = generate_input_object_metainfo_json(obj, parent, name_stack)
    container.append(json)


#===============================================================================
def generate_input_object_metainfo_json(child, parent, name_stack):
    path = ".".join(name_stack)
    json_obj = {}
    json_obj["name"] = "x_cp2k_{}.{}".format(path, child.name)
    json_obj["superNames"] = ["x_cp2k_{}".format(path)]

    # Description
    description = child.description
    if description is None or description.isspace():
        description = "Settings for {}".format(child.name)
    json_obj["description"] = description

    # Shape
    # data_dim = int(child.data_dimension)
    # if data_dim == -1:
        # data_dim = "n"
    # if data_dim == 1:
        # json_obj["shape"] = []
    # else:
        # json_obj["shape"] = [data_dim]
    json_obj["shape"] = []

    # Determine data type according to xml info
    mapping = {
        "keyword": "C",
        "logical": "C",
        "string": "C",
        "integer": "C",
        "word": "C",
        "real": "C",
    }
    json_obj["dtypeStr"] = mapping[child.data_type]
    return json_obj


#===============================================================================
def generate_section_metainfo_json(child, parent, name_stack):
    name = ".".join(name_stack)
    path = ".".join(name_stack[:-1])
    json_obj = {}

    json_obj["name"] = "x_cp2k_{}".format(name)
    json_obj["kindStr"] = "type_section"
    json_obj["superNames"] = ["x_cp2k_{}".format(path)]

    description = child.description
    if description is None or description.isspace():
        description = "Settings for {}".format(child.name)
    json_obj["description"] = description
    return json_obj


#===============================================================================
# Run main function by default
if __name__ == "__main__":

    # xml to pickle
    # xml_file = open("../versions/cp2k262/input_data/cp2k_input.xml", 'r')
    # object_tree = CP2KInput(generate_object_tree(xml_file))
    # file_name = "../versions/cp2k262/input_data/cp2k_input_tree.pickle"
    # fh = open(file_name, "wb")
    # pickle.dump(object_tree, fh, protocol=2)

    # Metainfo generation
    xml_file = open("../versions/cp2k262/input_data/cp2k_input.xml", 'r')
    object_tree = CP2KInput(generate_object_tree(xml_file, for_metainfo=True))
    generate_input_metainfos(object_tree)
