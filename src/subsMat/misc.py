#!/usr/bin/env python
# coding: utf-8

import copy
import glob
import json
import numpy as np
import os
import re
import uuid
from pathlib import Path
from typing import Union, List, Sequence
from collections import Counter

from monty.io import reverse_readfile

from pymatgen.core.composition import Composition
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.cif import CifWriter
from pymatgen.core.periodic_table import Element, Specie, DummySpecie

from pymongo import MongoClient


def element_list(species):
    """make species of material

    helper subroutine

    Parameters
    ----------
    species: a list of atomic species
        material species

    Returns
    -------
    species: dict (Structure.species)
    """
    counter = Counter(species)
    elementlist = []
    for x in counter:
        elementlist.append([str(x), counter[x]])
    return elementlist

