import unittest
import os
from cp2kparser.implementation.autoparser import get_parser
from cp2kparser.generics.util import *
# import logging
# logging.basicConfig(level=logging.DEBUG)


#===============================================================================
class TestFunctionals(unittest.TestCase):

    def getxc(self, folder, result):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "functionals", folder)
        parser = get_parser(path)
        xc = parser.get_quantity("XC_functional")
        self.assertEqual(xc, result)

    def test_pade(self):
        self.getxc("pade", "LDA_XC_TETER93")

    def test_lda(self):
        self.getxc("lda", "LDA_XC_TETER93")

    def test_becke88(self):
        self.getxc("becke88", "GGA_X_B88")

    def test_blyp(self):
        self.getxc("blyp", "GGA_C_LYP_GGA_X_B88")

if __name__ == '__main__':
    unittest.main()
