from cp2kparser.engines.regexengine import Regex


#===============================================================================
class CP2KRegexs(object):
    """Definitions of regular expression objects for CP2K. The regexengine
    defined in nomadparser.engines.regexengine can interpret these type of
    objects into sensible queries.
    """

    energy_total = Regex(
        r'''
        \sENERGY\|\ Total.*:\s+  # The preamble
        ([-+]?\d*\.\d+)   	 # The actual numeric value
        ''',
        separator=r'\n',
        direction="up",
        index=0,
        from_beginning=True)

    particle_forces = Regex(
        r'''
        \n\n
        \ \#\ Atom\s+Kind\s+Element\s+X\s+Y\s+Z\n
        ((?:
        \s+\d+\s+\d+\s+\w+
        (?:\s+[-+]?\d*\.\d+)+
        \n)+)
        \ SUM\ OF\ ATOMIC\ FORCES
        ''',
        separator=r" ATOMIC FORCES in",
        direction="down",
        index="all",
        from_beginning=False)


#===============================================================================
class CP2K_240_Regexs(CP2KRegexs):
    def __init__(self):
        CP2KRegexs.__init__(self)
