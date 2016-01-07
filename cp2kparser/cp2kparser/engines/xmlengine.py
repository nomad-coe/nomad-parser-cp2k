"""
This engine is used to parse XML files using XPath commands
(http://www.w3.org/TR/xpath/). It uses the cElementTree package, but it could
be easily replaced with another XML parsing package that implements the
ElemenTree API such as lxml.
"""

import xml.etree.cElementTree as ET


#===============================================================================
class XMLEngine(object):
    """Used to parse out XML content.
    """
    def __init__(self, parser):
        """
        Args:
            cp2k_parser: Instance of a NomadParser or it's subclass. Allows
            access to e.g. unified file reading methods.
        """
        self.parser = parser

    def parse(self, contents, XPath):

        # Open the XML differently depending on whether it is string of a file
        # handle
        if isinstance(contents, (str, unicode)):
            tree = ET.fromstring(contents)
        elif isinstance(contents, file):
            tree = ET.parse(contents)
        else:
            tree = contents
            return tree.findall(XPath)

        # Get the path
        return tree.getroot().findall(XPath)
