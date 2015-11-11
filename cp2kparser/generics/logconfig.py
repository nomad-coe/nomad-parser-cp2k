"""
This module is used to control the logging of the parser.

Each module in the package can have it's own logger, so that you can control
the logging on a modular level easily.

If you want to use a logger on a module simply add the following in the module
preamble:
    import logging
    logger = logging.getLogger(__name__)

This creates a logger with a hierarchical name. The hierarchical name allows
the logger to inherit logger properties from a parent logger, but also allows
module level control for logging.

A custom formatting is also used for the log messages. The formatting is done
by the LogFormatter class and is different for different levels.
"""
import logging
import textwrap


#===============================================================================
class LogFormatter(logging.Formatter):

    def format(self, record):
        level = record.levelname
        module = record.module
        message = record.msg

        if level == "INFO" or level == "DEBUG":
            return make_titled_message("{}:{}".format(level, module), message)
        else:
            return "\n        " + make_title("WARNING", width=64) + "\n" + make_message(message, width=64, spaces=8) + "\n"


#===============================================================================
def make_titled_message(title, message, width=80, spaces=0):
    """Styles a message to be printed into console.
    """
    wrapper = textwrap.TextWrapper(width=width-6)
    lines = wrapper.wrap(message)
    styled_message = ""
    first = True
    for line in lines:
        if first:
            new_line = spaces*" " + "  >> {}: ".format(title) + line + (width-6-len(line))*" " + "  "
            styled_message += new_line
            first = False
        else:
            new_line = spaces*" " + "     " + line + (width-6-len(line))*" " + "  "
            styled_message += "\n" + new_line
    return styled_message


#===============================================================================
def make_message(message, width=80, spaces=0):
    """Styles a message to be printed into console.
    """
    wrapper = textwrap.TextWrapper(width=width-6)
    lines = wrapper.wrap(message)
    styled_message = ""
    first = True
    for line in lines:
        new_line = spaces*" " + "|  " + line + (width-6-len(line))*" " + "  |"
        if first:
            styled_message += new_line
            first = False
        else:
            styled_message += "\n" + new_line
    styled_message += "\n" + spaces*" " + "|" + (width-2)*"-" + "|"
    return styled_message


#===============================================================================
def make_title(title, width=80):
    """Styles a title to be printed into console.
    """
    space = width-len(title)-4
    pre_space = space/2-1
    post_space = space-pre_space
    line = "|" + str((pre_space)*"=") + " "
    line += title
    line += " " + str((post_space)*"=") + "|"
    return line


#===============================================================================
# The highest level logger setup
root_logger = logging.getLogger("cp2kparser")
root_logger.setLevel(logging.INFO)

# Create console handler and set level to debug
root_console_handler = logging.StreamHandler()
root_console_handler.setLevel(logging.DEBUG)
root_console_formatter = LogFormatter()
root_console_handler.setFormatter(root_console_formatter)
root_logger.addHandler(root_console_handler)
