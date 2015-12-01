#! /usr/bin/env python
import cp2kparser.generics.logconfig
from pint import UnitRegistry
import os
ureg = UnitRegistry(os.path.dirname(__file__)+"/unit_registry.txt")
