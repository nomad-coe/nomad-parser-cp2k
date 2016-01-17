import os
import logging
from nomadcore.local_meta_info import loadJsonFile
import nomadtoolkit.utils.config
from nomadtoolkit.analysis.local_backend import LocalBackend


logger = logging.getLogger(__name__)


class Analyzer(object):
    def __init__(self, parser=None):
        self.parser = parser

        # Use a local backend with the default metainfos
        if not parser.parser_context.backend:
            metadir = nomadtoolkit.utils.config.get_config("metaInfoPath")
            default_metainfo_path = os.path.realpath(os.path.join(metadir, parser.get_metainfo_filename()))
            metainfoenv, warnings = loadJsonFile(default_metainfo_path)
            backend = LocalBackend(metainfoenv)
            parser.parser_context.backend = backend

    def parse(self):
        if not self.parser:
            logger.error("A parser hasn't been defined.")
        self.parser.parse()

        return self.parser.parser_context.backend.results


if __name__ == "__main__":

    # Initialize backend
    metainfo_path = "/home/lauri/Dropbox/nomad-dev/nomad-meta-info/meta_info/nomad_meta_info/cp2k.nomadmetainfo.json"
    metainfoenv, warnings = loadJsonFile(metainfo_path)
    backend = LocalBackend(metainfoenv)
    # backend = JsonParseEventsWriterBackend(metainfoenv, sys.stdout)

    # Initialize parser
    from cp2kparser import CP2KParser
    dirpath = "/home/lauri/Dropbox/nomad-dev/parser-cp2k/cp2kparser/cp2kparser/tests/cp2k_2.6.2/forces/outputfile/n"
    parser = CP2KParser(dirpath=dirpath, metainfo_path=metainfo_path, backend=backend)

    # Initialize analyzer
    analyser = Analyzer(parser)
    results = analyser.parse()

    # Get Results
    xc = results["XC_functional"]
    # temps = results["cp2k_md_temperature_instantaneous"]
    print xc.values
