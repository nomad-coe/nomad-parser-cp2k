import sys
import os
baseDir = os.path.dirname(os.path.abspath(__file__))
commonDir = os.path.normpath(os.path.join(baseDir, "../../../../python-common/common/python"))

if os.path.exists(commonDir):
    if not commonDir in sys.path:
        sys.path.insert(0, commonDir)
