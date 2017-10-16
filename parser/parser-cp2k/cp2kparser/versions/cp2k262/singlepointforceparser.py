import logging
import numpy as np
from nomadcore.baseclasses import AbstractBaseParser
logger = logging.getLogger("nomad")


class CP2KSinglePointForceParser(AbstractBaseParser):
    """Used to parse out a force file printed out by a CP2K single point
    calculation. It is not exactly an ZYX file, so here we define separate
    parser.
    """
    def __init__(self, file_path, parser_context):
        super(CP2KSinglePointForceParser, self).__init__(file_path, parser_context)

    def parse(self):
        start = False
        forces = []
        with open(self.file_path) as f:
            for line in f:
                if line.startswith(" # Atom"):
                    start = True
                    continue
                elif line.startswith(" SUM"):
                    forces = np.array(forces)
                    self.backend.addArrayValues("atom_forces", forces, unit="forceAu")
                    break
                elif start:
                    components = [float(comp) for comp in line.split()[-3:]]
                    forces.append(components)
