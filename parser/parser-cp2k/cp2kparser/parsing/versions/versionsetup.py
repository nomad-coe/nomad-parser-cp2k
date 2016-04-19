
"""Returns the implementation classes based on the given version identifier.
The different version are grouped into subpackages.
"""
import importlib
import logging
logger = logging.getLogger(__name__)


def get_main_parser(version_id):

    # Currently the version id is a pure integer, so it can directly be mapped
    # into a package name.
    base = "cp2kparser.parsing.versions.cp2k{}.".format(version_id)
    try:
        main_parser = importlib.import_module(base + "mainparser").CP2KMainParser
    except ImportError:
        logger.debug("A parser with the version id '{}' could not be found. Defaulting to the base implementation based on CP2K 2.6.2.".format(version_id))
        base = "cp2kparser.parsing.versions.cp2k262."
        main_parser = importlib.import_module(base + "mainparser").CP2KMainParser
    return main_parser
