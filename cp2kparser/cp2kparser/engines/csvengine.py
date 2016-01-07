import numpy as np
import logging
logger = logging.getLogger(__name__)
from io import StringIO
try:
    import re2 as re
except ImportError:
    import re
    logger.warning((
        "re2 package not found. Using re package instead. "
        "If you wan't to use re2 please see the following links:"
        "    https://github.com/google/re2"
        "    https://pypi.python.org/pypi/re2/"
    ))
else:
    re.set_fallback_notification(re.FALLBACK_WARNING)


#===============================================================================
class CSVEngine(object):
    """Used to parse out freeform CSV-like content.
    Currently only can parse floating point information.

    Reads the given file or string line by line, ignoring commented sections.
    Each line with data is split with a given delimiter expression (regex).
    From the split line the specified columns will be returned as floating
    point numbers in a numpy array.

    If given a separator specification (regex), the algorithm will try to split
    the contents into different configurations which will be separated by a
    line that matches the separator.
    """

    def __init__(self, parser):
        """
        Args:
            cp2k_parser: Instance of a NomadParser or it's subclass. Allows
            access to e.g. unified file reading methods.
        """
        self.parser = parser

    def iread(self, contents, columns, delimiter=r"\s+", comments=r"#", separator=None):
        """Used to iterate a CSV-like file. If a separator is provided the file
        is iterated one configuration at a time. Only keeps one configuration
        of the file in memory. If no separator is given, the whole file will be
        handled.

        The contents are separated into configurations whenever the separator
        regex is encountered on a line.
        """

        def split_line(line):
            """Chop off comments, strip, and split at delimiter.
            """
            if line.isspace():
                return None
            if comments:
                line = compiled_comments.split(line, maxsplit=1)[0]
            line = line.strip('\r\n ')
            if line:
                return compiled_delimiter.split(line)
            else:
                return []

        def is_separator(line):
            """Check if the given line matches the separator pattern.
            Separators are used to split a file into multiple configurations.
            """
            if separator:
                return compiled_separator.search(line)
            return False

        # If string or unicode provided, create stream
        if isinstance(contents, (str, unicode)):
            contents = StringIO(unicode(contents))

        # Precompile the different regexs before looping
        if comments:
            comments = (re.escape(comment) for comment in comments)
            compiled_comments = re.compile('|'.join(comments))
        if separator:
            compiled_separator = re.compile(separator)
        compiled_delimiter = re.compile(delimiter)

        # Columns as list
        if columns is not None:
            columns = list(columns)

        # Start iterating
        configuration = []
        for line in contents:  # This actually reads line by line and only keeps the current line in memory

            # If separator encountered, yield the stored configuration
            if is_separator(line):
                if configuration:
                    yield np.array(configuration)
                    configuration = []
            else:
                # Ignore comments, separate by delimiter
                vals = split_line(line)
                line_forces = []
                if vals:
                    for column in columns:
                        try:
                            value = vals[column]
                        except IndexError:
                            logger.warning("The given index '{}' could not be found on the line '{}'. The given delimiter or index could be wrong.".format(column, line))
                            return
                        try:
                            value = float(value)
                        except ValueError:
                            logger.warning("Could not cast value '{}' to float. Currently only floating point values are accepted".format(value))
                            return
                        else:
                            line_forces.append(value)
                    configuration.append(line_forces)

        # The last configuration is yielded even if separator is not present at
        # the end of file or is not given at all
        if configuration:
            yield np.array(configuration)
