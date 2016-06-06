import importlib
import logging
logger = logging.getLogger("nomad")


#===============================================================================
def get_main_parser(version_id, run_type):
    """
    Setups a main parser class for this calculation. The main class can be
    different for each version and run type.

    Args:
        version_id: An integer representing the CP2K version. The version
            number is originally a string the form '2.6.2', but here the numbers
            are just concatenated into a single integer number 262.
        run_type: A string that identifies the RUN_TYPE for the calculation.
            All the possible run types can be found in the CP2K reference manual.

    Returns:
        A python class that should be instantiated later with the correct
        parameters.
    """

    # Search for a RUN_TYPE specific parser
    parser_map = {
        "ENERGY": "SinglePointParser",
        "ENERGY_FORCE": "SinglePointParser",
        "WAVEFUNCTION_OPTIMIZATION": "SinglePointParser",
        "WFN_OPT": "SinglePointParser",
        "GEO_OPT": "GeoOptParser",
        "GEOMETRY_OPTIMIZATION": "GeoOptParser",
        "MD": "MDParser",
        "MOLECULAR_DYNAMICS": "MDParser",
    }
    try:
        parser = parser_map[run_type]
    except KeyError:
        logger.exception("A parser corresponding to the run_type '{}' could not be found.".format(run_type))
        raise

    # Currently the version id is a pure integer, so it can directly be mapped
    # into a package name.
    base = "cp2kparser.versions.cp2k{}.{}".format(version_id, parser.lower())
    parser_module = None
    parser_class = None
    try:
        parser_module = importlib.import_module(base)
    except ImportError:
        logger.warning("Could not find a parser for version '{}' and run type '{}'. Trying to default to the base implementation for CP2K 2.6.2".format(version_id, run_type))
        base = "cp2kparser.versions.cp2k262.{}".format(parser.lower())
        try:
            parser_module = importlib.import_module(base)
        except ImportError:
            logger.exception("Tried to default to the CP2K 2.6.2 implementation but could not find the correct modules for run_type '{}'.".format(run_type))
            raise
    try:
        parser_class = getattr(parser_module, "CP2K{}".format(parser))
    except AttributeError:
        logger.exception("A parser class '{}' could not be found in the module '[]'.".format(parser_class, parser_module))
        raise

    return parser_class
