"""
Setups the python-common library in the PYTHONPATH system variable.
"""
import sys
import os
import os.path

baseDir = os.path.dirname(os.path.abspath(__file__))
commonDir = os.path.normpath(os.path.join(baseDir, "../../../../../python-common/common/python"))
parserDir = os.path.normpath(os.path.join(baseDir, "../../parser-cp2k"))

# Using sys.path.insert(1, ...) instead of sys.path.insert(0, ...) based on
# this discusssion:
# http://stackoverflow.com/questions/10095037/why-use-sys-path-appendpath-instead-of-sys-path-insert1-path
if commonDir not in sys.path:
    sys.path.insert(1, commonDir)
if parserDir not in sys.path:
    sys.path.insert(1, parserDir)
