#!/usr/bin/env python
# coding: utf-8

from collections import Counter


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
