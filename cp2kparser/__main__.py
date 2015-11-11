#! /usr/bin/env python
import os
import logging
from cp2kparser.implementation.autoparser import get_parser

# logging.basicConfig(level=logging.INFO)
path = os.getcwd()
parser = get_parser(path)
parser.get_all_quantities()
