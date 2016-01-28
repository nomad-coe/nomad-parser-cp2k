
"""Returns the implementation classes based on the given version identifier.
The different version are grouped into subpackages.
"""
import importlib


def get_implementation_class(version_id):

    # Currently the version id is a pure integer, so it can directly be mapped
    # into a package name.
    base = "cp2kparser.parsing.versions.cp2k{}.".format(version_id)
    implementation = importlib.import_module(base + "implementation").CP2KImplementation
    return implementation
