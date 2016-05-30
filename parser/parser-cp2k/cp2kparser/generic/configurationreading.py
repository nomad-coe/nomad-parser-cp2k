import ase.io
import ase.io.formats
import mdtraj as md
import mdtraj.formats
import numpy as np
import logging
logger = logging.getLogger("nomad")


#===============================================================================
def iread(filename, index=None, file_format=None):
    """
    """
    # Test if ASE can open the file
    ase_failed = False
    if file_format is None:
        file_format = ase.io.formats.filetype(filename)
    try:
        io = ase.io.formats.get_ioformat(file_format)
    except ValueError:
        ase_failed = True
    else:
        # Return the positions in a numpy array instead of an ASE Atoms object
        generator = ase.io.iread(filename, index, file_format)
        for atoms in generator:
            pos = atoms.positions
            yield pos

    if ase_failed:
        if file_format == "dcd":
            with mdtraj.formats.DCDTrajectoryFile(filename, mode="r") as f:
                empty = False
                while not empty:
                    (xyz, cell_len, cell_angle) = f.read(1)
                    if len(xyz) == 0:
                        empty = True
                    else:
                        pos = xyz[0]
                        yield pos
