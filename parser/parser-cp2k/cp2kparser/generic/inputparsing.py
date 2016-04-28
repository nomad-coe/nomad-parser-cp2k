import logging
from collections import defaultdict
logger = logging.getLogger("nomad")


#===============================================================================
class CP2KInput(object):
    """The contents of a CP2K simulation including default values and default
    units from the version-specific xml file.
    """

    def __init__(self, root_section):
        self.root_section = root_section

    @staticmethod
    def decode_cp2k_unit(unit):
        """Given a CP2K unit name, decode it as Pint unit definition.
        """
        map = {
            # Length
            "bohr": "bohr",
            "m": "meter",
            "pm": "picometer",
            "nm": "nanometer",
            "angstrom": "angstrom",

            # Angle
            "rad": "radian",
            "deg": "degree",

            #Energy
            "Ry": "rydberg"
        }
        pint_unit = map.get(unit)
        if pint_unit:
            return pint_unit
        else:
            logger.error("Unknown CP2K unit definition '{}'.".format(unit))

    def set_parameter(self, path, value):
        parameter, section = self.get_parameter_and_section(path)
        parameter.value = value

    def set_keyword(self, path, value):
        keyword, section = self.get_keyword_and_section(path)
        if keyword and section:
            keyword.value = value
        elif section is not None:
            # print "Saving default keyword at path '{}'".format(path)
            split_path = path.rsplit("/", 1)
            keyword = split_path[1]
            section.default_keyword += keyword + " " + value + "\n"

    def get_section(self, path):
        split_path = path.split("/")
        section = self.root_section
        for part in split_path:
            section = section.get_subsection(part)
            if not section:
                print "Error in getting section at path '{}'.".format(path)
                return None
        return section

    def get_keyword_and_section(self, path):
        split_path = path.rsplit("/", 1)
        keyword = split_path[1]
        section_path = split_path[0]
        section = self.get_section(section_path)
        keyword = section.get_keyword(keyword)
        if keyword and section:
            return (keyword, section)
        elif section:
            return (None, section)
        return (None, None)

    def get_keyword(self, path):
        """Returns the keyword that is specified by the given path.
        If the keyword has no value set, returns the default value defined in
        the XML.
        """
        keyword, section = self.get_keyword_and_section(path)
        if keyword:
            if keyword.value is not None:
                return keyword.get_value()
            else:
                # if section.accessed:
                return keyword.default_value

    def get_default_keyword(self, path):
        return self.get_section(path).default_keyword

    def set_section_accessed(self, path):
        section = self.get_section(path)
        section.accessed = True

    def get_keyword_default(self, path):
        keyword, section = self.get_keyword_and_section(path)
        if keyword:
            return keyword.default_value

    def get_default_unit(self, path):
        keyword, section = self.get_keyword_and_section(path)
        if keyword:
            return keyword.default_unit

    def get_unit(self, path):
        keyword, section = self.get_keyword_and_section(path)
        if keyword:
            return keyword.get_unit()

    def get_parameter_and_section(self, path):
        section = self.get_section(path)
        parameter = section.section_parameter
        return (parameter, section)

    def get_parameter(self, path):
        parameter, section = self.get_parameter_and_section(path)
        if parameter:
            if parameter.value:
                return parameter.value
            elif section and section.accessed:
                return parameter.lone_value


#===============================================================================
class Keyword(object):
    """Information about a keyword in a CP2K calculation.
    """
    __slots__ = ['value', 'unit', 'value_no_unit', 'default_name', 'default_value', 'default_unit']

    def __init__(self, default_name, default_value, default_unit_value):
        self.value = None
        self.unit = None
        self.value_no_unit = None
        self.default_name = default_name
        self.default_value = default_value
        self.default_unit = default_unit_value

    def get_value(self):
        """If the units of this value can be changed, return a value and the
        unit separately.
        """
        if self.default_unit:
            if not self.value_no_unit:
                self.decode_cp2k_unit_and_value()
            return self.value_no_unit
        else:
            return self.value

    def get_unit(self):
        if self.default_unit:
            if not self.unit:
                self.decode_cp2k_unit_and_value()
            return self.unit
        else:
            logger.error("The keyword '{}' does not have a unit.".format(self.default_name))

    def decode_cp2k_unit_and_value(self):
        """Given a CP2K unit name, decode it as Pint unit definition.
        """
        splitted = self.value.split(None, 1)
        unit_definition = splitted[0]
        if unit_definition.startswith('[') and unit_definition.endswith(']'):
            unit_definition = unit_definition[1:-1]
            self.unit = CP2KInput.decode_cp2k_unit(self.default_unit)
            self.value_no_unit = splitted[1]
        elif self.default_unit:
            logger.debug("No special unit definition found, returning default unit.")
            self.unit = CP2KInput.decode_cp2k_unit(self.default_unit)
            self.value_no_unit = self.value
        else:
            logger.debug("The value has no unit, returning bare value.")
            self.value_no_unit = self.value


#===============================================================================
class Section(object):
    """An input section in a CP2K calculation.
    """
    __slots__ = ['accessed', 'name', 'keywords', 'default_keyword', 'section_parameter', 'sections']

    def __init__(self, name):
        self.accessed = False
        self.name = name
        self.keywords = defaultdict(list)
        self.default_keyword = ""
        self.section_parameter = None
        self.sections = defaultdict(list)

    def get_keyword(self, name):
        keyword = self.keywords.get(name)
        if keyword:
            if len(keyword) == 1:
                return keyword[0]
            else:
                logger.error("The keyword '{}' in '{}' does not exist or has too many entries.".format(name, self.name))

    def get_subsection(self, name):
        subsection = self.sections.get(name)
        if subsection:
            if len(subsection) == 1:
                return subsection[0]
            else:
                logger.error("The subsection '{}' in '{}' has too many entries.".format(name, self.name))
        else:
            logger.error("The subsection '{}' in '{}' does not exist.".format(name, self.name))


#===============================================================================
class SectionParameters(object):
    """Section parameters in a CP2K calculation.

    Section parameters are the short values that can be added right after a
    section name, e.g. &PRINT ON, where ON is the section parameter.
    """
    __slots__ = ['value', 'default_value', 'lone_value']

    def __init__(self, default_value, lone_value):
        self.value = None
        self.default_value = default_value
        self.lone_value = lone_value
