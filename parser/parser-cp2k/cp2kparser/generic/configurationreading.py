import ase.io
import logging
logger = logging.getLogger("nomad")


#===============================================================================
def iread(filename, index=None, file_format=None):
    """
    """
    try:
        generator = ase.io.iread(filename, index, file_format)
    except ValueError:
        logger.error("ASE could not read the file '{}'.".format(filename))
        raise

    # Return the positions in a numpy array instead of the atoms object
    for atoms in generator:
        pos = atoms.positions
        yield pos
