import os
import logging
logger = logging.getLogger(__name__)

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
class Regex(object):
    """Represents a regex search used by the RegexEngine class.

    In addition to a regular regex object from the re2 or re  module, this
    object wraps additional information about a regex search:

        regex_string: The regular expression as a string. Supports also the
        more verbose form
        (https://docs.python.org/2/library/re.html#re.VERBOSE). Currently
        supports only one capturing group.

        index: Index for the wanted match. Can be a single integer number (also
        negative indices supported) or if the special value "all" is provided,
        all results will be returned.

        separator: If a separator is defined, the input file can be chopped
        into smaller pieces which are separated by the given separator. The
        separator is a strig representing a regular epression. The smaller pieces are
        then searched independently. This approach allows bigger files to be
        handled piece by piece without loading the whole file into memory.

        direction: If a separator is defined, this parameter defines whether
        the file is chopped into pieces starting from the end or from the
        start.

        from_beginning: If true, the input must match the regular expression
        right from the start. Any matches in the middle of the input are not
        searched.

    """

    def __init__(self, regex_string, index="all", separator=None, direction="down", from_beginning=False):
        self.regex_string = regex_string
        self.index = index
        self.separator = separator
        self.direction = direction
        self.from_beginning = from_beginning
        self.compiled_regex = None
        self.compiled_separator = None
        self.inner_regex = None

        self.check_input()
        self.compile()

    def set_inner_regex(self, inner_regex):
        self.inner_regex = inner_regex

    def compile(self):
        self.compiled_regex = re.compile(self.regex_string, re.VERBOSE)
        self.compiled_separator = re.compile(self.separator, re.VERBOSE)

    def check_input(self):
        if self.direction != "down" and self.direction != "up":
            logger.error("Unsupported direction value '{}' in a regex".format(self.direction))

    def match(self, string):
        return self.compiled_regex.match(string)

    def search(self, string):
        return self.compiled_regex.search(string)

    def findall(self, string):
        return self.compiled_regex.findall(string)

    def finditer(self, string):
        return self.compiled_regex.finditer(string)


#===============================================================================
class RegexEngine(object):
    """Used for parsing values values from files with regular expressions.
    """

    def __init__(self, parser):
        self.regexs = None
        self.results = {}
        self.regex_dict = {}
        self.target_dict = {}
        self.files = None
        self.extractors = None
        self.extractor_results = {}
        self.output = None
        self.regexs = None
        self.cache = {}

        self.compiled_regexs = {}
        self.file_contents = {}

    def parse(self, regex, file_handle):
        """Use the given regex to parse contents from the given file handle"""

        file_name = file_handle.name
        logger.debug("Searching regex in file '{}'".format(file_name))
        result = self.recursive_extraction(regex, file_handle)
        if result:
            return result

        # Couldn't find the quantity
        logger.debug("Could not find a result for {}.".format(regex.regex_string))

    def recursive_extraction(self, regex, data):
        """Goes through the exctractor tree recursively until the final
        extractor is found and returns the value given by it. The value can be
        of any dimension but contains only strings.
        """

        # # Early return with cached result
        # result = self.extractor_results.get(extractor_id)
        # if result:
            # return result

        result = None

        # If separator specified, do a blockwise search
        if regex.separator is not None:
            logger.debug("Going into blockwise regex search")
            result = self.regex_block_search(data, regex)
        # Regular string search
        else:
            logger.debug("Going into full regex search")
            result = self.regex_search_string(data, regex)

        # See if the tree continues
        if regex.inner_regex is not None:
            logger.debug("Entering next regex recursion level.")
            return self.recursive_extraction(regex.inner_regex, result)
        else:
            return result

    def regex_search_string(self, data, regex):
        """Do a regex search on the data. This loads the entire data into so it
        might not be the best option for big files. See 'regex_block_search'
        for reading the file piece-by-piece.
        """
        from_beginning = regex.from_beginning
        index = regex.index

        # If given a file object, read all as string
        if isinstance(data, file):
            data.seek(0)
            contents = data.read()
        else:
            contents = data

        result = None
        if from_beginning:
            logger.debug("Doing full string search from beginning.")
            return regex.match(contents)
        elif index == "all":
            logger.debug("Doing full string search for all results.")
            result = regex.findall(contents)
            if not result:
                logger.debug("No matches.")
        elif index >= 0:
            logger.debug("Doing full string search with specified index.")
            iter = regex.finditer(contents)
            i = 0
            while i <= index:
                try:
                    match = iter.next()
                except StopIteration:
                    if i == 0:
                        logger.debug("No results.")
                    else:
                        logger.debug("Invalid regex index.")
                    break
                if i == index:
                    result = match.groups()[0]
                i += 1
        elif index < 0:
            matches = regex.findall(contents)
            if not matches:
                logger.debug("No matches.")
            else:
                try:
                    result = matches[index]
                except IndexError:
                    logger.debug("Invalid regex index.")

        return result

    def regex_block_search(self, file_handle, regex):
        """Do a regex search on the data. This function can load the file piece
        by piece to avoid loading huge files into memory. The piece-wise search
        can also be used to search the file from bottom to up.
        """
        separator = regex.separator
        direction = regex.direction
        index = regex.index
        from_beginning = regex.from_beginning
        logger.debug("Doing blockwise search with separator: '{}', direction: '{}', from_beginning: '{}' and index '{}'".format(separator, direction, from_beginning, index))

        # Determine the direction in which the blocks are read
        if direction == "up":
            logger.debug("Searching from bottom to up.")
            generator = self.reverse_block_generator(file_handle, separator)
        elif direction == "down":
            logger.debug("Searching from up to bottom.")
            generator = self.block_generator(file_handle, separator)
        else:
            logger.error("Unknown direction specifier: {}".format(direction))
            return

        # If all results wanted, just get all results from all blocks
        if index == "all":
            logger.debug("Searchin for all matches.")
            results = []
            for block in generator:
                matches = regex.findall(block)
                if matches:
                    if isinstance(matches, list):
                        for match in matches:
                            results.append(match)
                    else:
                        results.append(matches.groups()[0])
            return results

        # If index given, search until the correct index found
        i_result = 0
        counter = 0
        for block in generator:
            logger.debug("Searchin for a specific index.")
            counter += 1
            if from_beginning:
                result = regex.match(block)
                if result:
                    logger.debug("Found match in beginning of block.")
                    if index + 1 > i_result + 1:
                        i_result += 1
                    else:
                        return result.groups()[0]
            else:
                results = regex.findall(block)
                if results:
                    if isinstance(results, list):
                        n_results = len(results)
                    else:
                        n_results = 1

                    logger.debug("Found results within block.")
                    if index + 1 > i_result + n_results:
                        i_result += n_results
                    else:
                        if n_results == 1:
                            return results.groups()[0]
                        else:
                            return results[i_result + (n_results-1) - index]

    def reverse_block_generator(self, fh, separator_pattern, buf_size=1000000):
        """A generator that returns chunks of a file piece-by-piece in reverse
        order.
        """
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        total_size = remaining_size = fh.tell()

        # Compile the separator with an added end of string character.
        compiled_separator = re.compile(separator_pattern)
        end_match = separator_pattern + r'$'
        compiled_end_match = re.compile(end_match)

        while remaining_size > 0:
            offset = min(total_size, offset + buf_size)
            fh.seek(-offset, os.SEEK_END)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            #print remaining_size
            lines = compiled_separator.split(buffer)
            # lines = buffer.split(separator)
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # If this chunk ends with the separator, do not concatenate
                # the segment to the last line of new chunk instead, yield the
                # segment instead
                if compiled_end_match.find(buffer):
                    yield segment
                else:
                    lines[-1] += segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if len(lines[index]):
                    yield lines[index]
        yield segment

    def block_generator(self, fh, separator_pattern, buf_size=1000000):
        """A generator that returns chunks of a file piece-by-piece
        """
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        total_size = remaining_size = fh.tell()
        fh.seek(0, os.SEEK_SET)

        #Compile regex
        compiled_separator = re.compile(separator_pattern)

        while remaining_size > 0:
            offset = min(total_size, offset)
            fh.seek(offset, os.SEEK_SET)
            offset += buf_size
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            parts = compiled_separator.split(buffer)
            # The last part of the buffer must be appended to the next chunk's first part.
            if segment is not None:
                # If this chunk starts right with the separator, do not concatenate
                # the segment to the first line of new chunk instead, yield the
                # segment instead
                if compiled_separator.match(buffer):
                    yield segment
                else:
                    parts[0] = segment + parts[0]
            segment = parts[-1]
            for index in range(0, len(parts) - 1, 1):
                if len(parts[index]):
                    yield parts[index]
        yield segment
